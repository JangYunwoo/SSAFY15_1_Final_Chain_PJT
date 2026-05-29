PROCESS_RULES = {
    "Edge-Ring": [
        ("ETCH", 92, "Edge 영역 집중 불량으로 식각 균일도와 척 상태를 우선 확인하세요."),
        ("CMP", 71, "외곽부 압력 편차 가능성이 있어 패드 마모와 압력 조건을 점검하세요."),
        ("PHOTO", 63, "노광 정렬 및 포커스 편차가 외곽 패턴에 영향을 줄 수 있습니다."),
    ],
    "Center": [
        ("CMP", 88, "중앙부 집중 불량은 압력/슬러리 분포 편차와 연관될 수 있습니다."),
        ("ETCH", 74, "챔버 중앙 플라즈마 밀도 조건을 점검하세요."),
        ("PHOTO", 58, "중앙부 포커스 조건을 확인하세요."),
    ],
    "Scratch": [
        ("CLEAN", 91, "스크래치 패턴은 이송/세정 장비 접촉 가능성이 높습니다."),
        ("CMP", 80, "패드 이물 또는 과압 조건을 확인하세요."),
        ("PHOTO", 45, "마스크/웨이퍼 표면 이물 가능성을 보조 점검하세요."),
    ],
    "Donut": [
        ("ETCH", 84, "링 형태 패턴은 가스 유량과 온도 분포 영향을 의심할 수 있습니다."),
        ("CMP", 72, "중앙-외곽 압력 분포를 확인하세요."),
        ("DEPO", 64, "증착 두께 균일도 로그를 점검하세요."),
    ],
    "Loc": [
        ("PHOTO", 83, "국소 불량은 오염, 포커스, 레티클 이슈를 우선 확인하세요."),
        ("CLEAN", 66, "국소 이물 제거 공정을 확인하세요."),
        ("ETCH", 54, "국소 플라즈마 이상 로그를 확인하세요."),
    ],
    "Random": [
        ("CLEAN", 76, "무작위 불량은 파티클/이물 가능성이 높습니다."),
        ("PHOTO", 68, "랜덤 결함은 노광 전 표면 상태 확인이 필요합니다."),
        ("DEPO", 52, "증착 공정 중 파티클 로그를 확인하세요."),
    ],
    "Edge-Loc": [
        ("ETCH", 89, "외곽 국소 결함은 Edge exclusion 조건과 클램프 영역을 확인하세요."),
        ("CMP", 69, "외곽 국소 압력 이상을 확인하세요."),
        ("CLEAN", 55, "외곽 이물 축적 가능성을 확인하세요."),
    ],
    "Near-full": [
        ("DEPO", 95, "전면 불량은 레시피/챔버 조건 이상 가능성이 커 즉시 확인이 필요합니다."),
        ("ETCH", 91, "전면 식각 조건 이상 여부를 점검하세요."),
        ("PHOTO", 82, "전체 노광 조건과 장비 상태를 확인하세요."),
    ],
}


def recommend_processes(label, confidence):
    rows = PROCESS_RULES.get(label, PROCESS_RULES["Random"])
    penalty = max(0, 0.9 - float(confidence)) * 10
    recommendations = []
    for rank, (process, score, reason) in enumerate(rows, start=1):
        adjusted = max(0, round(score - penalty, 2))
        recommendations.append(
            {
                "rank": rank,
                "process": process,
                "score": adjusted,
                "reason": reason,
                "stop_alert": adjusted >= 90,
            }
        )
    return recommendations


def build_summary(analysis):
    confidence = analysis.confidence_percent
    risk_text = "신뢰도가 낮아 커뮤니티 검토를 권장합니다." if analysis.is_low_confidence else "신뢰도가 양호하여 우선순위 기준 점검을 진행할 수 있습니다."
    top = analysis.recommendations.first()
    process_text = f"최우선 점검 공정은 {top.process}입니다." if top else "추천 공정이 아직 없습니다."
    return f"{analysis.predicted_label} 패턴으로 분류되었습니다. 신뢰도는 {confidence}%입니다. {process_text} {risk_text}"
