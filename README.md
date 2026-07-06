# Agentic Product Studio

`Agentic Product Studio`는 문서, WBS, 일정, 멤버 관리를 한 곳에서 운영하기 위한 내부 협업 도구입니다.

현재 권장 운영 구조는 아래와 같습니다.

- 프론트/UI: `Flask + Jinja2`
- 앱 데이터: `Cloudflare D1`
- 문서 이미지 스토리지: `Cloudflare R2`
- 배포 프론트 서버: `PythonAnywhere`

즉, 화면은 기존 Flask 웹을 그대로 사용하고, 데이터와 이미지 저장소만 Cloudflare를 사용하는 방식입니다.

## 현재 권장 아키텍처

```text
Browser
  -> PythonAnywhere Flask
      -> Cloudflare D1
      -> Cloudflare R2
```

이 구조를 권장하는 이유는 아래와 같습니다.

- 기존 Flask 템플릿과 화면을 그대로 유지할 수 있습니다.
- 유지보수가 쉽습니다.
- 브라우저에 Cloudflare 인증 정보를 노출하지 않아도 됩니다.
- CORS, 토큰 관리, 프론트 API 계약 복잡도를 줄일 수 있습니다.

## 주요 기능

- 대시보드
  - 진행 현황
  - 이번 주 마감 작업
  - 최근 문서 / 최근 작업 / 예정 일정
- WBS
  - 작업 생성 / 수정 / 삭제
  - 상위/하위 작업 구조
  - 담당자 / 상태 / 우선순위 / 진행률 관리
  - 문서 연결
- 문서
  - 문서 생성 / 수정 / 삭제 / 상세 보기
  - 폴더 / 태그 / 관련 작업 연결
  - Markdown 렌더링
  - R2 이미지 업로드 및 문서 자산 관리
- 일정
  - 일정 생성 / 수정 / 삭제
  - 담당자 / 연결 작업 관리
- 멤버
  - 멤버 생성 / 수정 / 삭제
  - 작업 / 일정 / 문서 작성자 참조 관리

## 저장소 구조

```text
agentic-product-studio/
├─ app/
│  ├─ __init__.py
│  ├─ dashboard.py
│  ├─ documents.py
│  ├─ wbs.py
│  ├─ schedules.py
│  ├─ members.py
│  ├─ storage.py
│  ├─ db.py
│  ├─ utils.py
│  ├─ constants.py
│  ├─ repositories/
│  ├─ static/
│  └─ templates/
├─ database/d1/
│  ├─ README.md
│  └─ schema.sql
├─ worker/
├─ worker-python/
├─ .docs/
├─ run.py
├─ requirements.txt
└─ .env.example
```

## Repository 구조

데이터 접근은 `repository provider` 구조로 분리되어 있습니다.

- `REPOSITORY_BACKEND=sqlite`
  - 로컬 SQLite 사용
- `REPOSITORY_BACKEND=d1`
  - Cloudflare D1 REST API 사용

스토리지는 아래처럼 분기됩니다.

- `STORAGE_BACKEND=local`
  - `uploads/` 사용
- `STORAGE_BACKEND=r2`
  - Cloudflare R2 사용

즉, Flask 화면 코드는 그대로 두고 백엔드 저장소만 교체할 수 있게 구성되어 있습니다.

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 준비

`.env.example`을 기준으로 `.env`를 구성합니다.

권장 운영값:

```env
STORAGE_BACKEND=r2
REPOSITORY_BACKEND=d1
```

필수 Cloudflare 관련 값:

- `CLOUDFLARE_ACCOUNT_ID`
- `D1_DATABASE_ID`
- `CLOUDFLARE_API_TOKEN`
- `R2_BUCKET_NAME`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_PUBLIC_BASE_URL`

### 3. 로컬 실행

```bash
python run.py
```

## 운영 체크

Cloudflare 연결 상태를 빠르게 확인하려면 아래 명령을 사용합니다.

```bash
flask cloudflare-check
```

예시:

```bash
FLASK_APP=run.py flask cloudflare-check
```

이 명령은 아래를 확인합니다.

- 현재 repository backend
- 현재 storage backend
- dashboard summary 조회 가능 여부
- active members 조회 가능 여부
- R2 public base URL 설정 여부

## PythonAnywhere 배포

실제 운영 배포는 Flask 프론트 + D1/R2 백엔드 기준으로 진행합니다.

상세 절차는 아래 문서를 참고하면 됩니다.

- [PYTHONANYWHERE_DEPLOY_PROCESS.md](/D:/dev/git/agentic-product-studio/PYTHONANYWHERE_DEPLOY_PROCESS.md)

PythonAnywhere 콘솔에서 빠르게 반영하려면 아래 스크립트를 사용할 수 있습니다.

```bash
bash scripts/pythonanywhere_refresh.sh
```

## Cloudflare 참고 문서

- [database/d1/README.md](/D:/dev/git/agentic-product-studio/database/d1/README.md)
- [.docs/cloudflare/README.md](/D:/dev/git/agentic-product-studio/.docs/cloudflare/README.md)

## 현재 운영 방향

현재 이 프로젝트의 권장 운영 방향은 아래와 같습니다.

1. Flask 웹은 그대로 유지
2. PythonAnywhere에서 Flask를 렌더링 서버로 사용
3. D1을 앱 데이터 저장소로 사용
4. R2를 이미지 저장소로 사용
5. Worker UI는 실험/이관 기록용으로만 유지

이 방향이 가장 유지보수 비용이 낮고, 기존 화면 품질도 가장 안정적으로 보존할 수 있습니다.
