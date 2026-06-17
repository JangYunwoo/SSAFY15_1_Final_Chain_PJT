# Wafer Insight

완성된 웨이퍼 결함 분류 모델을 활용해 LOT 단위 CSV를 분석하고, 분석 이력과 리포트, 커뮤니티, 알림/메일을 제공하는 Vue + Django 서비스입니다.

## 주요 기능

- LOT 단위 CSV 업로드 분석
- 지정 폴더 기반 LOT CSV 자동 분석
- 웨이퍼 결함 예측 및 공정 추천
- 분석 이력, 배치 상세, 분석 상세 조회
- 분석 결과 리포트 작성 및 커뮤니티 공유
- 알림/메일 관리

## 백엔드 실행

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

백엔드 주소:

```text
http://127.0.0.1:8000
```

## 프론트엔드 실행

다른 터미널에서 실행합니다.

```bash
npm install
npm run dev
```

프론트 주소:

```text
http://127.0.0.1:5173
```

## LOT CSV 자동 분석

자동 분석은 별도 터미널에서 실행합니다.

```bash
python manage.py watch_lot_folder
```

기본 감시 폴더:

```text
LotData/incoming
```

처리 결과:

- 성공한 CSV: `LotData/processed`
- 실패한 CSV: `LotData/failed`

CSV 안의 `lot_id`는 관리자 페이지에 등록된 LOT과 일치해야 합니다.

## CSV 형식

권장 형식:

```csv
lot_id,wafer_id,wafer_index,process,step,equipment_id,recipe_id,inspection_time,die_size,yield_rate,wafer_map
LOT20260617-DEMO,WAFER-001,1,ETCH,POST_ETCH,ETCH-03,RCP-ETCH-A,2026-06-17 09:30:00,1683,91.2,"[[0,0,0],[0,1,2],[0,0,0]]"
```

필수 컬럼:

- `lot_id`
- `wafer_map`

권장 컬럼:

- `wafer_id` 또는 `wafer_index`
- `process`
- `step`
- `equipment_id`
- `recipe_id`
- `inspection_time`
- `die_size`
- `yield_rate`

## 모델 파일

기본 모델 경로:

```text
models/best_radai_resnet.pt
```

모델 파일이 없거나 torch 로딩이 실패하면 개발용 fallback 예측으로 동작합니다.

---

## 2026-06-17 작업 요약

### 1. CSV 자동 분석 흐름 추가

- `LotData/incoming` 폴더에 CSV 파일이 들어오면 자동으로 분석되도록 watcher 기능을 추가했습니다.
- 분석이 완료된 CSV 파일은 `LotData/processed`로 이동합니다.
- 분석에 실패한 CSV 파일은 `LotData/failed`로 이동합니다.
- 실행 명령어:

```bash
python manage.py watch_lot_folder
```

### 2. 분석 업로드 기능 변경

- 프론트의 분석 업로드 화면에서 CSV를 업로드하면 내부적으로 `LotData/incoming`에 저장되도록 변경했습니다.
- 실제 분석은 watcher가 해당 파일을 감지해서 처리합니다.
- 사용자 화면에서는 기존처럼 `업로드 및 분석` 흐름으로 보이도록 문구를 유지했습니다.

### 3. 분석 결과 Top 3 표시

- 기존에는 분석 결과에서 1위 예측값과 신뢰도만 표시했습니다.
- 모델이 계산한 전체 클래스 확률을 DB에 저장하도록 `probabilities_json` 필드를 추가했습니다.
- 분석 세부페이지에서 예측 결과를 1위, 2위, 3위까지 표시하도록 변경했습니다.
- 기존 분석 데이터도 다시 계산해서 Top 3 확률이 보이도록 반영했습니다.

### 4. 분석 세부페이지 표시 개선

- 분석 세부페이지의 공정명 표시를 정리했습니다.
- 예: `ETCH`, `PHOTO` -> `Etch`, `Photo`
- DB 값은 변경하지 않고 프론트 화면에서만 보기 좋게 변환합니다.

### 5. 실행 시 주의사항

- 로컬 개발 시에는 아래 3개를 각각 실행해야 합니다.

```bash
python manage.py runserver
npm run dev
python manage.py watch_lot_folder
```

- 새 마이그레이션이 추가되었으므로 처음 받는 환경에서는 아래 명령어를 실행해야 합니다.

```bash
python manage.py migrate
```

- 모델 파일은 Git에 포함하지 않으므로 별도로 아래 위치에 넣어야 합니다.

```text
models/best_radai_resnet.pt
```

한 줄 요약: CSV 업로드/폴더 감지 기반 자동 분석 흐름을 추가했고, 분석 세부 결과에서 모델 예측 Top 3 확률을 확인할 수 있도록 개선했습니다.
