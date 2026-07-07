# Agentic Product Studio

`Agentic Product Studio`는 문서, WBS, 일정, 멤버 관리를 한 곳에서 운영하기 위한 내부 협업 도구입니다.

현재 프로젝트는 아래 구조를 기준으로 운영합니다.

- 프론트/UI: `React + MUI` 정적 빌드
- 앱 서버: `Flask`
- 앱 데이터: `Cloudflare D1` 또는 `SQLite`
- 문서 이미지 스토리지: `Cloudflare R2` 또는 로컬 `uploads/`
- 배포 프론트 서버: `PythonAnywhere`

## 현재 아키텍처

```text
Browser
  -> PythonAnywhere Flask
      -> React build (app/static/frontend)
      -> /api/*
      -> /documents/preview-markdown
      -> /documents/format-markdown
      -> /documents/search-links
      -> /documents/upload-image
      -> Cloudflare D1 or SQLite
      -> Cloudflare R2 or local uploads
```

이 구조를 사용하는 이유는 아래와 같습니다.

- 화면은 React로 분리해 UI 유지보수를 쉽게 가져갈 수 있습니다.
- Flask는 API와 업로드/미리보기 유틸 엔드포인트에 집중할 수 있습니다.
- PythonAnywhere에서는 빌드 결과물만 서빙하면 되므로 운영이 단순합니다.
- D1/R2로 저장소를 분리해 배포 유연성을 확보할 수 있습니다.

## 주요 화면 경로

- `/`
- `/documents`
- `/wbs`
- `/schedules`
- `/members`

기존 `/app/*`, `/document/*`, `/task/*`, `/schedule/*`, `/member/*` 경로는 현재 새 경로로 리다이렉트됩니다.

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
  - 이미지 업로드 / 문서 자산 관리
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
│  ├─ api.py
│  ├─ documents.py
│  ├─ frontend.py
│  ├─ storage.py
│  ├─ db.py
│  ├─ utils.py
│  ├─ constants.py
│  ├─ repositories/
│  └─ static/frontend/
├─ frontend/
│  ├─ src/
│  └─ package.json
├─ database/d1/
│  ├─ README.md
│  └─ schema.sql
├─ .docs/
├─ run.py
├─ requirements.txt
├─ package.json
└─ .env.example
```

## 데이터/스토리지 백엔드

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

## 빠른 시작

### 1. Python 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 프론트 의존성 설치

```bash
npm run frontend:install
```

### 3. 환경 변수 준비

`.env.example`을 기준으로 `.env`를 구성합니다.

예시:

```env
REPOSITORY_BACKEND=d1
STORAGE_BACKEND=r2
```

Cloudflare 사용 시 주요 값:

- `CLOUDFLARE_ACCOUNT_ID`
- `D1_DATABASE_ID`
- `CLOUDFLARE_API_TOKEN`
- `R2_BUCKET_NAME`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_PUBLIC_BASE_URL`

### 4. 프론트 빌드

```bash
npm run frontend:build
```

### 5. 로컬 실행

```bash
python run.py
```

## 프론트 개발

개발 중에는 Vite 개발 서버를 따로 띄울 수 있습니다.

```bash
npm run frontend:dev
```

최종 반영은 항상 아래 빌드 결과 기준입니다.

```bash
npm run frontend:build
```

빌드 결과물은 `app/static/frontend/`에 생성됩니다.

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

PythonAnywhere에서는 보통 아래 순서로 반영합니다.

1. 로컬에서 프론트 빌드
2. 빌드 결과 포함해서 커밋/푸시
3. PythonAnywhere에서 `git pull`
4. 앱 reload

빠른 반영용 스크립트:

```bash
bash scripts/pythonanywhere_refresh.sh
```

기본 virtualenv 이름이 다르면 아래처럼 지정할 수 있습니다.

```bash
VENV_NAME=<your_virtualenv_name> bash scripts/pythonanywhere_refresh.sh
```

상세 절차:

- [PYTHONANYWHERE_DEPLOY_PROCESS.md](/D:/dev/git/agentic-product-studio/PYTHONANYWHERE_DEPLOY_PROCESS.md)

## 참고 문서

- [database/d1/README.md](/D:/dev/git/agentic-product-studio/database/d1/README.md)
- [.docs/frontend/frontend-refactoring-milestone.md](/D:/dev/git/agentic-product-studio/.docs/frontend/frontend-refactoring-milestone.md)
- [.docs/README.md](/D:/dev/git/agentic-product-studio/.docs/README.md)
