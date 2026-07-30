# Agentic Product Studio

`Agentic Product Studio`는 외부 에셋 카탈로그 개발팀이 문서, WBS, 일정, 멤버, Assets를 한 곳에서 관리하기 위한 내부 협업용 웹앱입니다.

이 서비스는 사용자가 브라우저에서 직접 사용하는 협업 도구이면서, 동시에 AI Agent가 기획 문서와 운영 데이터를 확인하며 개발 작업을 진행할 때 참조하는 작업 허브 역할도 합니다.

현재 운영 기준은 `FastAPI + React(MUI)` 애플리케이션을 Docker로 패키징하고, Oracle Cloud VM의 Nginx 뒤에서 실행하는 구조입니다. 데이터와 파일은 각각 Cloudflare D1과 R2를 사용하며, Cloudflare DNS/Proxy가 외부 진입점 역할을 담당합니다.

![Agentic Product Studio Architecture Overview](./Overview.svg)

## 현재 운영 구조

```text
User
  -> Cloudflare DNS / Proxy / TLS
      -> Oracle VM
          -> Nginx :80/:443
              -> Docker Compose
                  -> Uvicorn + FastAPI :8000
                      -> React build (app/static/frontend)
                      -> API (/api/*)
                      -> Markdown utility endpoints (/documents/*)
                      -> Cloudflare D1 / SQLite shadow
                      -> Cloudflare R2 / local uploads fallback

AI Agent
  -> Static guides (.docs/catalog/*)
  -> HTTP API (/api/*, /documents/*)
      -> Cloudflare Proxy
          -> Nginx
              -> FastAPI
                  -> D1-backed documents / project data
                  -> Markdown helper endpoints
```

이 구조를 쓰는 이유는 아래와 같습니다.

- 프론트는 React로 분리해 화면 리팩토링과 UI 유지보수를 쉽게 가져갑니다.
- FastAPI는 API, 업로드, Markdown 유틸, SPA 서빙을 담당하는 기본 런타임입니다.
- Nginx는 HTTPS를 종료하고 애플리케이션 포트 `127.0.0.1:8000`으로 요청을 전달합니다.
- Docker 이미지는 특정 클라우드 런타임에 종속되지 않으며, 일반 Docker 환경에서도 실행할 수 있습니다.
- Flask는 기존 명령과 호환 실행을 위한 legacy 경로로만 유지합니다.
- 데이터와 스토리지를 D1/R2로 분리해 실행 서버를 교체해도 운영 데이터를 유지할 수 있습니다.
- AI Agent는 `.docs/catalog/` 가이드와 운영 API를 함께 참조해, 최신 기획 문맥과 구현 대상 데이터를 확인하며 작업할 수 있습니다.

## 사용자와 AI Agent의 역할

- 사용자는 브라우저에서 대시보드, 문서, WBS, 일정, 멤버, 에셋 관리 화면을 직접 사용합니다.
- FastAPI 앱은 React 프론트엔드와 API를 함께 서빙하며, 문서 미리보기/업로드 같은 보조 엔드포인트도 제공합니다.
- `run.py`와 Flask blueprint는 ASGI 운영 검증이 끝날 때까지 호환 경로로 유지합니다.
- AI Agent는 `.docs/catalog/`의 정적 가이드를 먼저 읽고, 필요하면 운영 API를 조회해 최신 문서와 데이터를 다시 확인합니다.
- 즉, 이 서비스는 단순한 내부 웹앱이 아니라, 사용자와 AI가 같은 문서/데이터 기반 위에서 협업하는 개발 허브로 동작합니다.

## 주요 기능

- 대시보드
  - 진행 현황
  - 이번 주 마감 작업
  - 최근 문서 / 최근 WBS 업데이트 / 예정 일정 / 공지 확인
- 문서
  - 생성 / 수정 / 삭제 / 상세 보기
  - 폴더 / 태그 / 숨김 문서 관리
  - 관련 WBS 연결
  - Markdown 렌더링
  - 이미지 업로드 및 문서 자산 연결
- Assets
  - Assets 목록 / 상세 / 등록 / 수정 / 삭제
  - 그룹(폴더) 트리 관리
  - 태그 / 상태 / 유형 / 등록자 관리
  - Cloudflare R2 또는 로컬 파일 연동
- WBS
  - 작업 생성 / 수정 / 삭제
  - 상위 / 하위 작업 구조
  - 담당자 / 상태 / 우선순위 / 진행률 / 완료일 관리
  - 문서 연결
- 일정
  - 일정 생성 / 수정 / 삭제
  - 일정 유형 / 담당자 / 연결 작업 관리
- 멤버
  - 멤버 생성 / 수정 / 삭제
  - 작업 / 일정 / 문서 작성자 참조 관리
- 로그
  - `/log` 경로에서 페이지 접속 로그 조회

## 주요 경로

- `/`
- `/dashboard`
- `/documents`
- `/assets`
- `/wbs`
- `/schedules`
- `/members`
- `/log`

레거시 경로는 현재 아래처럼 리다이렉트됩니다.

- `/app/*`
- `/document/*`
- `/asset/*`
- `/task/*`
- `/schedule/*`
- `/member/*`
- `/logs`

## 기술 스택

- Frontend: `React`, `React Router`, `MUI`, `Vite`
- Backend: `FastAPI` (`Flask` legacy compatibility)
- Database:
  - `SQLite` 로컬 개발/보조 저장
  - `Cloudflare D1` 운영 데이터 저장소
- Storage:
  - `Cloudflare R2`
  - 또는 로컬 `uploads/`
- Infra / Deploy:
  - `Docker` / `Docker Compose`
  - Oracle Cloud VM (Ubuntu)
  - `Nginx` reverse proxy
  - `Uvicorn` ASGI server
  - Cloudflare DNS / Proxy / D1 / R2

## 디렉터리 개요

```text
agentic-product-studio/
├─ app/
│  ├─ __init__.py              # Flask legacy app factory / config
│  ├─ api.py                   # React frontend용 API
│  ├─ frontend.py              # React build 서빙 및 라우팅
│  ├─ documents.py             # Markdown 유틸 / 업로드 관련 엔드포인트
│  ├─ db.py                    # SQLite schema / migration helper
│  ├─ storage.py               # local / R2 파일 저장소 처리
│  ├─ repositories/            # sqlite / d1 repository provider 레이어
│  └─ static/frontend/         # Docker build 시 생성되는 Vite 결과물
├─ frontend/
│  ├─ src/
│  └─ package.json
├─ database/d1/
│  ├─ README.md
│  └─ schema.sql
├─ scripts/
├─ deployment/
│  └─ oracle/                  # Oracle VM Compose 실행 예시와 배포 안내
├─ .docs/                      # 개발용 내부 문서 / 회고 / 마일스톤
├─ uploads/
├─ instance/                   # 로컬 SQLite DB / page view 로그 등 런타임 파일
├─ worker/                     # Cloudflare Worker 관련 레거시/실험 코드
├─ worker-python/              # Cloudflare Python Worker 관련 레거시 설정/코드
├─ run.py
├─ requirements.txt
├─ package.json
├─ wrangler.toml
├─ wrangler.toml.example
└─ .env.example
```

## 데이터 / 저장소 백엔드

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

## 스키마 기준

로컬 SQLite와 D1은 DB 파일 자체보다 아래 스키마 정의를 기준으로 관리합니다.

- 로컬 SQLite 앱 스키마/초기화/마이그레이션:
  - [app/db.py](app/db.py)
  - `SCHEMA_SQL`과 `init_db()`, `migrate_legacy_schema()`가 로컬 `app.db` 구조를 정의합니다.
- Cloudflare D1 baseline 스키마:
  - [database/d1/schema.sql](database/d1/schema.sql)
  - Wrangler/D1 반영 시 기준이 되는 정식 SQL 스키마입니다.

즉, `instance/app.db` 같은 런타임 SQLite 파일은 생성 결과물이고, 구조의 정식 기준은 위 두 파일입니다.

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

`.env.example`을 기준으로 `.env`를 작성합니다.

주의:

- `.env.example`의 `DATABASE={}` / `UPLOAD_FOLDER={}`는 "비워둔 자리" 표시입니다.
- 로컬 기본 경로를 그대로 쓰려면 해당 줄을 삭제하거나, 실제 경로로 명시해서 사용하세요.
- 값을 비우지 않고 `{}` 그대로 두면 문자열 `"{}"` 경로를 사용하게 됩니다.

최소 예시:

```env
SECRET_KEY=dev
REPOSITORY_BACKEND=sqlite
STORAGE_BACKEND=local
DISPLAY_TIMEZONE=Asia/Seoul
```

Cloudflare 연동 시 주요 값:

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

### 5. 로컬 DB 초기화

로컬 SQLite는 앱이 처음 뜰 때 자동 생성되지만, 명시적으로 초기화하거나 샘플 데이터를 넣고 시작하려면 아래 명령을 사용합니다.

스키마만 초기화:

```bash
flask --app run.py init-db
```

샘플 협업 데이터 주입:

```bash
flask --app run.py seed-sample-data
```

이미 데이터가 있는데 샘플 데이터를 다시 채우려면:

```bash
flask --app run.py seed-sample-data --force
```

정리:

- `init-db`는 테이블/컬럼 등 스키마만 준비합니다.
- `seed-sample-data`는 멤버, WBS, 문서, 일정, 공지 샘플 데이터를 넣습니다.
- `instance/app.db`는 런타임 생성물이라 레포에 포함하지 않아도 됩니다.

### 6. 로컬 실행

```bash
python run.py
```

기본 로컬 주소:

- `http://localhost:5000`

## 프론트 개발

개발 중에는 Vite 개발 서버를 따로 띄울 수 있습니다.

```bash
npm run frontend:dev
```

로컬에서 정적 파일을 확인해야 할 때만 아래 명령을 실행합니다.

```bash
npm run frontend:build
```

`app/static/frontend/`는 배포 산출물이므로 Git에 커밋하지 않습니다. 운영 Docker image를 빌드할 때 Dockerfile의 Node build stage가 프론트 소스를 빌드해 최종 이미지에 포함합니다.

## 운영 / 점검 명령

Cloudflare 연결 상태를 빠르게 확인하려면 아래 명령을 사용합니다.

```bash
flask cloudflare-check
```

예시:

```bash
FLASK_APP=run.py flask cloudflare-check
```

PowerShell 예시:

```powershell
$env:FLASK_APP="run.py"
flask cloudflare-check
```

이 명령은 아래를 확인합니다.

- 현재 repository backend
- 현재 storage backend
- dashboard summary 조회 가능 여부
- active members 조회 가능 여부
- R2 public base URL 설정 여부

## 실행 엔트리포인트

현재 저장소에는 두 가지 앱 진입점이 있습니다.

- `asgi.py`
  - FastAPI 운영/이관 대상 엔트리포인트
- `run.py`
  - 기존 Flask 호환 엔트리포인트

로컬에서 FastAPI를 실행하려면 아래처럼 사용합니다.

```bash
uvicorn asgi:app --reload
```

Docker로 실행하려면 아래처럼 사용할 수 있습니다.

```bash
docker build -t personal-service-fastapi .
docker run --rm -p 8000:8000 --env-file .env personal-service-fastapi
```

운영 환경에서는 `.env` 파일을 이미지에 포함하지 말고, 호스팅 플랫폼의 런타임 환경변수/Secret 기능으로 주입합니다. 이 이미지는 Cloudflare Container뿐 아니라 일반 Docker 호스팅에서도 사용할 수 있습니다.

간단한 래퍼 스크립트를 쓰고 싶다면 아래도 가능합니다.

```bash
python fastapi_run.py
```

## 운영 배포

현재 운영 배포는 Oracle Cloud VM에서 Docker Compose로 수행합니다.

상세 절차는 [deployment/oracle/README.md](deployment/oracle/README.md)를 참고하세요.

핵심 실행 구조는 다음과 같습니다.

```text
Cloudflare DNS / Proxy
  -> Nginx :443
      -> 127.0.0.1:8000
          -> Docker Compose
              -> Uvicorn + FastAPI
```

운영 환경변수는 VM의 `.env`에 직접 주입하며, 저장소나 Docker 이미지에 포함하지 않습니다. D1 API Token과 R2 S3 Access Key도 각각 필요한 최소 권한으로 관리합니다.

배포 브랜치를 갱신한 뒤에는 VM에서 다음처럼 컨테이너를 재생성합니다.

```bash
git pull origin master
docker compose -f deployment/oracle/docker-compose.yml up -d --build --force-recreate
```

## PythonAnywhere legacy 배포

PythonAnywhere용 Flask 설정은 legacy 호환 경로로만 남아 있습니다.

현재 운영 전환 대상은 `run.py`가 아니라 `asgi.py`입니다. FastAPI를 지원하는 ASGI 호스팅 환경에서 Uvicorn 등의 서버로 실행해야 합니다.

ASGI 서버 예시는 [deployment/asgi_uvicorn.example.txt](deployment/asgi_uvicorn.example.txt)에 정리해두었습니다.

PythonAnywhere legacy 환경의 일반적인 반영 순서는 아래와 같습니다.

1. 소스 커밋 / 푸시
2. ASGI 호스팅 환경에서 `git pull`
3. 필요 시 환경 변수와 DB 초기화 확인
4. ASGI 프로세스 재시작

Flask 호환 실행은 마이그레이션 검증이나 기존 CLI가 필요한 경우에만 사용합니다.

```bash
python run.py
```

Flask 제거는 ASGI 운영 검증과 FastAPI 기반 테스트가 끝난 뒤 별도 작업으로 진행합니다.

PythonAnywhere legacy 환경에서만 사용하는 빠른 반영용 스크립트:

```bash
bash scripts/pythonanywhere_refresh.sh
```

virtualenv 이름이 다르면 아래처럼 지정할 수 있습니다.

```bash
VENV_NAME=<your_virtualenv_name> bash scripts/pythonanywhere_refresh.sh
```

## 현재 참고 사항

- 시간 표시는 프론트에서 `Asia/Seoul` 기준으로 변환해 보여줍니다.
- React 빌드 청크는 Docker build 때 생성되며, `app/static/frontend/` 산출물은 Git 추적 대상이 아닙니다.
- `instance/app.db`는 로컬/보조용 SQLite이며, 운영 데이터 기준은 D1을 우선으로 봅니다.
