# Wafer Insight

Django Template 기반 반도체 웨이퍼맵 분류/점검 우선순위 추천 서비스 초안입니다.

## 핵심 기능

- ResNet 기반 웨이퍼맵 결함 분류 업로드/분석
- LLM 또는 규칙 기반 공정 점검 우선순위 추천
- 분석 상세/히스토리/모델 성능 화면
- 분석 결과 보고서 작성, 인쇄, 커뮤니티 게시
- 낮은 신뢰도 분석 결과를 토론할 수 있는 커뮤니티
- 알림/메일/프로필/관리자 관리 화면 초안

## 설치

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 모델 파일

기본 모델 경로는 프로젝트 폴더 기준 `models/best_radai_resnet.pt`입니다.

```env
WAFER_MODEL_PATH=models\best_radai_resnet.pt
```

모델/torch가 없으면 개발용 규칙 기반 더미 예측으로 동작하도록 만들어 두었습니다.

## 업로드 CSV 형식

양산공정 기준 기본 업로드는 LOT 단위 CSV입니다. 파일 하나가 하나의 LOT 검사 배치이고, 한 행은 웨이퍼 1장을 의미합니다.

```csv
lot_id,wafer_id,wafer_index,process,step,equipment_id,recipe_id,inspection_time,die_size,yield_rate,wafer_map
LOT20260529-001,WAFER-001,1,ETCH,POST_ETCH,ETCH-03,RCP-ETCH-A,2026-05-29 09:30:00,1683,91.2,"[[0,0,0],[0,1,2],[0,0,0]]"
LOT20260529-001,WAFER-002,2,ETCH,POST_ETCH,ETCH-03,RCP-ETCH-A,2026-05-29 09:33:00,1683,88.5,"[[0,0,0],[1,1,2],[0,0,0]]"
```

필수 컬럼:

- `lot_id`
- `wafer_id` 또는 `wafer_index`
- `wafer_map`

권장 컬럼:

- `process`
- `step`
- `equipment_id`
- `recipe_id`
- `inspection_time`
- `die_size`
- `yield_rate`

업로드 시 선택한 담당 LOT과 CSV의 `lot_id`가 다르면 분석을 중단합니다. 예시는 `samples/sample_lot_batch.csv`를 참고하세요.

### 보조 형식: 웨이퍼맵 행렬만 있는 CSV

```csv
0,0,1,1,2,0
0,1,1,2,2,0
0,1,2,2,1,0
0,0,1,1,0,0
```

- 각 행은 같은 개수의 열을 가져야 합니다.
- 값은 숫자여야 합니다. 일반적으로 `0`, `1`, `2` 형태의 die 상태 값을 사용합니다.
- 서버에서 자동으로 `64x64`로 리사이즈하고 정규화한 뒤 모델에 입력합니다.

단건 테스트용 예시는 `samples/sample_wafer_map.csv`를 참고하세요.

### 보조 형식: 노트북 데이터프레임을 CSV로 저장한 형식

`waferMap` 컬럼 한 칸에 2차원 배열이 들어간 CSV도 지원합니다. 여러 행이 있으면 현재는 첫 번째 행의 `waferMap`을 분석합니다.

```csv
waferMap,dieSize,lotName,waferIndex,trainTestLabel,failureType
"[[0,0,0],[0,1,2],[0,0,0]]",1683.0,lot1,1.0,"[[Training]]","[[none]]"
```

예시는 `samples/sample_wafer_dataframe.csv`를 참고하세요.
