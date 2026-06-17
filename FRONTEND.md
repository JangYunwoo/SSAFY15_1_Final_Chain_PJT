# Vue + Django Development

이 프로젝트는 Vue 프론트엔드와 Django 백엔드를 분리해서 실행합니다.

## 1. Django 백엔드 실행

터미널 1에서 가상환경을 활성화합니다.

```bash
venv\Scripts\activate
```

Django 서버를 실행합니다.

```bash
python manage.py runserver
```

백엔드 주소:

```text
http://127.0.0.1:8000
```

## 2. Vue 프론트엔드 실행

터미널 2에서 프론트 개발 서버를 실행합니다.

```bash
npm run dev
```

프론트 주소:

```text
http://127.0.0.1:5173
```

브라우저는 프론트 주소로 접속합니다.

## API 연결

Vue 개발 서버는 `vite.config.js`의 proxy 설정으로 Django API 요청을 `http://127.0.0.1:8000`으로 전달합니다.

사용 중인 주요 API 경로:

- `/accounts/api/*`
- `/api/dashboard/`
- `/analyses/api/*`
- `/community/api/*`
- `/reports/api/*`
- `/notifications/api/*`
- `/media/*`

## LOT CSV 자동 분석

자동 분석용 폴더 구조:

```text
LotData/
  incoming/
  processed/
  failed/
```

별도 터미널에서 감시 명령을 실행합니다.

```bash
python manage.py watch_lot_folder
```

`LotData/incoming/`에 CSV 파일을 넣으면 자동으로 분석합니다.

- 분석 성공: `LotData/processed/`로 이동
- 분석 실패: `LotData/failed/`로 이동

CSV의 `lot_id`는 DB에 등록된 `Lot ID`와 일치해야 합니다.
