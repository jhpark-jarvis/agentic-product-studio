# Agentic Product Studio

`Agentic Product Studio`는 외부 에셋 카탈로그 개발팀을 위한 내부 협업용 웹앱입니다.

이 프로젝트는 `Flask + SQLite` 기반으로 만들어졌으며, 아래 같은 업무를 한곳에서 관리하는 것을 목표로 합니다.

- 개발 문서 공유
- WBS 기반 작업 관리
- 일정 공유
- 팀원 정보 관리
- 문서와 작업 연결 추적

현재 구조는 작은 개발팀이 빠르게 운영할 수 있는 내부 도구를 기준으로 설계되어 있습니다.

## 주요 기능

- 대시보드
- WBS 작업 관리
- 문서 작성 및 공유
- 일정 관리
- 팀원 관리

## 프로젝트 구조

```text
agentic-product-studio/
  app.py
  requirements.txt
  README.md
  DEPLOY_PROCESS.md
  PYTHONANYWHERE_DEPLOY_PROCESS.md

  app/
    __init__.py
    constants.py
    db.py
    utils.py

    dashboard.py
    wbs.py
    documents.py
    schedules.py
    members.py

    static/
      styles.css

    templates/
      base.html

      dashboard/
        index.html

      wbs/
        list.html
        form.html

      documents/
        list.html
        form.html
        detail.html

      schedules/
        list.html
        form.html

      members/
        list.html
        form.html

  instance/
    app.db

  uploads/
```

## 구조 설명

### `app.py`

애플리케이션 실행용 엔트리 포인트입니다.

### `app/__init__.py`

Flask 앱 팩토리입니다.

- 앱 설정 로드
- 업로드 경로 생성
- 블루프린트 등록
- DB 초기화

### `app/db.py`

SQLite 스키마와 DB 유틸리티를 담당합니다.

- 테이블 생성
- 기존 문서 테이블 마이그레이션
- 태그/문서 연결 동기화
- 샘플 데이터 생성 CLI

### `app/constants.py`

상태값, 우선순위, 문서 유형, 일정 유형 같은 공통 상수를 관리합니다.

### `app/utils.py`

날짜 처리와 Markdown 렌더링 같은 공통 유틸리티를 제공합니다.

### `app/dashboard.py`

메인 대시보드 라우트를 담당합니다.

### `app/wbs.py`

WBS 작업 목록, 생성, 수정, 삭제와 필터링 로직을 담당합니다.

### `app/documents.py`

문서 목록, 검색, 상세, 생성, 수정, 삭제 기능을 담당합니다.

### `app/schedules.py`

일정 목록, 주간/월간 보기, 생성, 수정, 삭제 기능을 담당합니다.

### `app/members.py`

팀원 목록과 기본 CRUD를 담당합니다.

### `app/templates/`

Jinja2 템플릿 폴더입니다.

- `base.html`: 공통 레이아웃
- `dashboard/`: 대시보드 화면
- `wbs/`: WBS 화면
- `documents/`: 문서 화면
- `schedules/`: 일정 화면
- `members/`: 팀원 화면

### `app/static/styles.css`

전체 관리자형 UI 스타일을 담당합니다.

### `instance/app.db`

SQLite 데이터베이스 파일입니다.

### `uploads/`

업로드 파일 저장용 디렉터리입니다.

## 라우트 개요

- `/` : 대시보드
- `/wbs` : WBS 작업 관리
- `/documents` : 문서 관리
- `/schedules` : 일정 관리
- `/members` : 팀원 관리

## 참고 문서

- [DEPLOY_PROCESS.md](D:/dev/git/agentic-product-studio/DEPLOY_PROCESS.md)
- [PYTHONANYWHERE_DEPLOY_PROCESS.md](D:/dev/git/agentic-product-studio/PYTHONANYWHERE_DEPLOY_PROCESS.md)
