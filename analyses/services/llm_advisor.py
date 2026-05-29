def build_llm_prompt(analysis, recommendations):
    rec_text = "\n".join(
        [f"{item['rank']}. {item['process']} - score {item['score']}: {item['reason']}" for item in recommendations]
    )
    return f"""반도체 웨이퍼맵 결함 분석 결과를 바탕으로 점검 우선순위 보고 문장을 작성해 주세요.

분석 ID: {analysis.analysis_code}
예측 결함: {analysis.predicted_label}
신뢰도: {analysis.confidence_percent}%
수율 기준: {analysis.yield_threshold}%

추천 후보:
{rec_text}

요구사항:
- 현장 엔지니어가 바로 확인할 수 있게 간결하게 작성
- 신뢰도가 낮으면 커뮤니티 논의를 권장
- 장비 중단 검토가 필요한 경우 명확히 표현
"""


def generate_advice(analysis, recommendations):
    # OpenAI, GMS, FastAPI 기반 LLM 서버를 붙일 때 이 함수만 교체하면 됩니다.
    top = recommendations[0] if recommendations else None
    confidence_text = "추가 검토가 필요합니다" if analysis.is_low_confidence else "우선순위 판단에 활용 가능합니다"
    if not top:
        return f"{analysis.predicted_label} 분석 결과가 생성되었지만 추천 공정이 없어 담당자 확인이 필요합니다."
    return (
        f"{analysis.predicted_label} 패턴으로 분류되었고 신뢰도는 {analysis.confidence_percent}%입니다. "
        f"1순위 점검 공정은 {top['process']}이며, {top['reason']} "
        f"현재 결과는 {confidence_text}."
    )
