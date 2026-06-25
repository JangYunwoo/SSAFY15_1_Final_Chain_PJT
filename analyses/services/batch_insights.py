"""Batch-level analysis and optional GMS chat completion integration."""

import json
from collections import Counter

import requests

from django.conf import settings
from django.utils import timezone


def build_batch_context(analyses):
    analyses = list(analyses)
    normalized_labels = []
    abnormal_labels = []
    for item in analyses:
        is_normal = item.effective_yield_rate is not None and item.effective_yield_rate >= 90
        label = "Normal" if is_normal else item.predicted_label or "Unknown"
        normalized_labels.append(label)
        if not is_normal:
            abnormal_labels.append(label)

    labels = Counter(normalized_labels)
    abnormal_distribution = Counter(abnormal_labels)
    normal_count = labels["Normal"]
    return {
        "wafer_count": len(analyses),
        "normal_count": normal_count,
        "normal_rate": round(normal_count / len(analyses) * 100, 1) if analyses else 0,
        "label_distribution": dict(labels),
        "abnormal_distribution": dict(abnormal_distribution),
        "lots": sorted({item.lot.lot_id for item in analyses if item.lot_id}),
        "processes": sorted({item.process for item in analyses if item.process}),
    }


def fallback_insight(context):
    labels = context["label_distribution"]
    primary = max(labels, key=labels.get) if labels else "분석 결과 없음"
    normal = context["normal_count"]
    total = context["wafer_count"]
    text = f"총 {total}장의 웨이퍼를 분석했습니다. 가장 많이 분포한 패턴은 {primary}입니다."
    if normal:
        text += f" 수율 90% 이상 정상 처리 웨이퍼는 {normal}장입니다."
    recommendations = [{"rank": 1, "process": "검토 필요", "reason": "GMS_KEY를 설정하면 배치 분포를 기반으로 한 AI 공정 추천이 제공됩니다."}]
    report = f"배치 분석 보고서\n\n{text}\n\n라벨 분포: " + ", ".join(f"{label} {count}장" for label, count in labels.items())
    return {"summary": text, "recommendations": recommendations, "report": report, "is_fallback": True}


def request_gms_insight(context):
    fallback = fallback_insight(context)
    if not settings.GMS_KEY:
        return fallback

    from analyses.models import GmsConnectionState

    state, _ = GmsConnectionState.objects.get_or_create(pk=1)
    if state.is_circuit_open:
        return fallback

    prompt = (
        "다음 반도체 웨이퍼 CSV 배치의 집계 결과를 분석해 주세요. "
        "개별 웨이퍼가 아니라 연속적인 분포를 근거로 점검 공정을 추천하세요. "
        "JSON만 반환하세요: summary(문자열), recommendations([{rank,process,reason}]), report(문자열).\n"
        + json.dumps(context, ensure_ascii=False)
    )
    payload = {
        "model": settings.GMS_MODEL,
        "messages": [
            {
                "role": "developer",
                "content": (
                    "Answer in Korean. Return valid JSON only. Produce a detailed semiconductor process-engineering "
                    "Use label_distribution, where Normal means yield >= 90%. Use normal_rate to assess overall "
                    "batch stability, but base process recommendations primarily on abnormal_distribution. "
                    "assessment of roughly 700-900 completion tokens. summary should be 450-650 Korean characters "
                    "and explain the dominant distribution, likely mechanism, and risk. Provide exactly 4 ranked "
                    "recommendations; each reason should be 180-280 Korean characters with concrete inspection items, "
                    "evidence from the distribution, and priority rationale. report should be 1,000-1,400 Korean characters "
                    "and include distribution percentages, interpretation, probable causes, a stepwise verification plan, "
                    "and an action recommendation. Do not use markdown outside the JSON values."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    try:
        response = requests.post(
            settings.GMS_API_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.GMS_KEY}",
            },
            timeout=(15, settings.GMS_TIMEOUT),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(content)
        if not isinstance(result.get("recommendations"), list):
            raise ValueError("invalid recommendations")
        state.failure_count = 0
        state.last_error = ""
        state.save(update_fields=["failure_count", "last_error", "updated_at"])
        return {**fallback, **result, "is_fallback": False}
    except (requests.RequestException, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
        state.is_circuit_open = True
        state.failure_count += 1
        state.last_error = str(exc)[:1000]
        state.save(update_fields=["is_circuit_open", "failure_count", "last_error", "updated_at"])
        # 응답 전달 실패 뒤 재시도하지 않는다. 이미 완료된 추론에 대해 중복 과금될 수 있다.
        return fallback


def create_batch_insight(batch, user, analyses=None, is_custom=False):
    """Create or replace the latest shared CSV insight after classification."""
    from analyses.models import BatchInsight

    analyses = analyses if analyses is not None else batch.wafer_analyses.all()
    context = build_batch_context(analyses)
    try:
        result = request_gms_insight(context)
    except Exception:
        # 어떤 GMS 전송 예외도 배치 결과 저장 자체를 막아서는 안 된다.
        result = fallback_insight(context)
    created_at = timezone.localtime(batch.created_at)
    fields = {
        "title": f"{created_at:%Y-%m-%d %H:%M} 분석데이터" + (" (커스텀)" if is_custom else ""),
        "label_distribution": context["label_distribution"],
        "recommendation_text": result["summary"],
        "recommendations_json": result["recommendations"],
        "report_body": result["report"],
        "is_custom": is_custom,
        "is_fallback": result["is_fallback"],
    }
    queryset = BatchInsight.objects.filter(batch=batch, user=user, is_custom=is_custom).order_by("-created_at")
    successful_insight = queryset.filter(is_fallback=False).first()
    # 새 호출이 fallback이면 이미 확보한 실제 GMS 응답을 덮어쓰지 않는다.
    if result["is_fallback"] and successful_insight:
        return successful_insight
    insight = queryset.first()
    if insight:
        for field, value in fields.items():
            setattr(insight, field, value)
        insight.save(update_fields=[*fields.keys()])
    else:
        insight = BatchInsight.objects.create(batch=batch, user=user, **fields)
    insight.analyses.set(analyses)
    return insight


def create_custom_analysis(user, analyses):
    from analyses.models import CustomAnalysis

    analyses = list(analyses)
    context = build_batch_context(analyses)
    try:
        result = request_gms_insight(context)
    except Exception:
        result = fallback_insight(context)
    custom = CustomAnalysis.objects.create(
        user=user,
        title=f"커스텀 분석 {timezone.localtime():%Y-%m-%d %H:%M}",
        label_distribution=context["label_distribution"],
        recommendation_text=result["summary"],
        recommendations_json=result["recommendations"],
        report_body=result["report"],
        is_fallback=result["is_fallback"],
    )
    custom.analyses.set(analyses)
    return custom
