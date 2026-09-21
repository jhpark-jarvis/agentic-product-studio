# Architecture

Agentic Product Studio는 하나의 제품 문맥을 사람과 AI Agent가 함께 읽고 갱신할 수 있도록 웹 UI, API, 데이터 계층과 저장소 문서를 결합합니다.

## Runtime

```text
React client
  -> FastAPI routers
      -> repository contracts
          -> SQLite repository
          -> D1 REST repository
      -> storage contract
          -> local uploads
          -> R2 object storage
```

- React는 업무 화면과 사용자 상호작용을 담당합니다.
- FastAPI는 JSON API, Markdown 도구, 파일 업로드와 SPA 제공을 담당합니다.
- repository provider는 로컬 개발과 클라우드 데이터 계층을 분리합니다.
- storage provider는 메타데이터와 실제 파일 저장 위치를 분리합니다.
- Flask 앱은 데이터 초기화와 가져오기 같은 기존 CLI를 유지합니다.

## Data ownership

- 스키마는 `app/db.py`와 `database/d1/schema.sql`이 정의합니다.
- SQLite 파일, 업로드 결과물과 프론트 빌드는 런타임 산출물이며 Git에 포함하지 않습니다.
- 실제 Secret은 환경 변수나 배포 플랫폼의 Secret 저장소에서만 주입합니다.
- 외부 카탈로그는 별도 어댑터 경계 뒤에 두어 특정 공급자에 종속되지 않게 합니다.

## Public portfolio boundary

공개판에는 재현 가능한 구조와 일반화된 예제만 포함합니다. 실제 운영 도메인, 인프라 식별자, 고객·팀 데이터, 비공개 기획, 접근 정책과 공급자 전용 API 계약은 포함하지 않습니다.

