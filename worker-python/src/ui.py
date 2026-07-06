from __future__ import annotations


def render_homepage() -> str:
    return """<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Agentic Product Studio</title>
    <style>
      :root {
        --bg: #eef3fb;
        --panel: rgba(255, 255, 255, 0.9);
        --panel-strong: #ffffff;
        --text: #1c2440;
        --muted: #65728f;
        --line: rgba(28, 36, 64, 0.11);
        --primary: #145dff;
        --primary-soft: rgba(20, 93, 255, 0.12);
        --accent: #10b981;
        --warn: #f59e0b;
        --danger: #ef4444;
        --radius: 22px;
        --shadow: 0 18px 40px rgba(20, 93, 255, 0.08);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        color: var(--text);
        font-family: "Segoe UI", "Noto Sans KR", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(20, 93, 255, 0.18), transparent 26%),
          radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 22%),
          linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
      }

      button, input, select, textarea {
        font: inherit;
      }

      button {
        cursor: pointer;
      }

      .page {
        width: min(1480px, calc(100vw - 28px));
        margin: 0 auto;
        padding: 18px 0 48px;
      }

      .hero,
      .workspace {
        background: var(--panel);
        backdrop-filter: blur(18px);
        border: 1px solid var(--line);
        border-radius: 28px;
        box-shadow: var(--shadow);
      }

      .hero {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 20px;
        padding: 24px;
      }

      .eyebrow {
        margin: 0 0 10px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: var(--primary);
        text-transform: uppercase;
      }

      .hero h1 {
        margin: 0;
        font-size: clamp(32px, 4vw, 54px);
        line-height: 1.04;
      }

      .hero p {
        margin: 14px 0 0;
        color: var(--muted);
        line-height: 1.7;
        font-size: 15px;
      }

      .hero-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 24px;
      }

      .button {
        border: 0;
        border-radius: 999px;
        padding: 12px 18px;
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary), #6993ff);
        color: #fff;
      }

      .button.secondary {
        background: rgba(28, 36, 64, 0.06);
        color: var(--text);
      }

      .status-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .status-card {
        padding: 16px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(28, 36, 64, 0.08);
      }

      .status-card .label {
        display: block;
        margin-bottom: 8px;
        color: var(--muted);
        font-size: 12px;
      }

      .status-card .value {
        font-size: 22px;
        font-weight: 900;
      }

      .workspace {
        margin-top: 18px;
        display: grid;
        grid-template-columns: 240px minmax(0, 1fr);
        min-height: 840px;
        overflow: hidden;
      }

      .sidebar {
        padding: 18px;
        border-right: 1px solid var(--line);
        background: rgba(16, 24, 40, 0.02);
      }

      .sidebar-title {
        margin: 0 0 8px;
        font-size: 14px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }

      .nav {
        display: grid;
        gap: 8px;
      }

      .nav button {
        width: 100%;
        border: 1px solid rgba(28, 36, 64, 0.08);
        background: rgba(255, 255, 255, 0.72);
        color: var(--text);
        border-radius: 16px;
        padding: 14px 14px;
        text-align: left;
        font-weight: 800;
      }

      .nav button.active {
        background: linear-gradient(135deg, rgba(20, 93, 255, 0.95), rgba(105, 147, 255, 0.95));
        color: #fff;
        border-color: transparent;
      }

      .sidebar-note {
        margin-top: 16px;
        padding: 16px;
        border-radius: 18px;
        background: rgba(20, 93, 255, 0.08);
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }

      .content {
        padding: 22px;
      }

      .tab {
        display: none;
      }

      .tab.active {
        display: block;
      }

      .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 14px;
        margin-bottom: 16px;
      }

      .tab-header h2 {
        margin: 0;
        font-size: 28px;
      }

      .tab-header p {
        margin: 8px 0 0;
        font-size: 14px;
        color: var(--muted);
      }

      .meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .pill {
        padding: 9px 12px;
        border-radius: 999px;
        background: rgba(28, 36, 64, 0.05);
        color: var(--muted);
        font-size: 12px;
        font-weight: 800;
      }

      .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
      }

      .panel {
        border-radius: var(--radius);
        border: 1px solid var(--line);
        background: var(--panel-strong);
        overflow: hidden;
      }

      .panel-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        padding: 18px;
        border-bottom: 1px solid var(--line);
      }

      .panel-head h3 {
        margin: 0;
        font-size: 16px;
      }

      .panel-head span {
        color: var(--muted);
        font-size: 12px;
      }

      .panel-body {
        padding: 18px;
      }

      .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
      }

      .summary-box {
        padding: 16px;
        border-radius: 18px;
        background: rgba(20, 93, 255, 0.06);
      }

      .summary-box .label {
        display: block;
        color: var(--muted);
        font-size: 12px;
        margin-bottom: 8px;
      }

      .summary-box .value {
        font-size: 24px;
        font-weight: 900;
      }

      .stack {
        display: grid;
        gap: 12px;
      }

      .feed-item {
        padding: 14px 15px;
        border-radius: 18px;
        background: rgba(28, 36, 64, 0.04);
        border: 1px solid rgba(28, 36, 64, 0.06);
      }

      .feed-item strong {
        display: block;
        margin-bottom: 6px;
        font-size: 14px;
      }

      .feed-item .meta {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
      }

      .form-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .field {
        display: grid;
        gap: 6px;
      }

      .field.full {
        grid-column: 1 / -1;
      }

      .field label {
        font-size: 12px;
        font-weight: 800;
        color: var(--muted);
      }

      .field input,
      .field select,
      .field textarea {
        width: 100%;
        padding: 12px 13px;
        border-radius: 14px;
        border: 1px solid rgba(28, 36, 64, 0.12);
        background: #fff;
      }

      .field textarea {
        min-height: 120px;
        resize: vertical;
      }

      .checkbox {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
      }

      .form-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 16px;
      }

      .table-wrap {
        overflow: auto;
      }

      .table {
        width: 100%;
        border-collapse: collapse;
      }

      .table th,
      .table td {
        padding: 12px 10px;
        border-bottom: 1px solid var(--line);
        text-align: left;
        vertical-align: top;
        font-size: 13px;
      }

      .table th {
        color: var(--muted);
        font-size: 12px;
      }

      .table tr:last-child td {
        border-bottom: 0;
      }

      .row-title {
        font-weight: 800;
      }

      .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 900;
      }

      .badge.done { background: rgba(16, 185, 129, 0.14); color: #067647; }
      .badge.progress { background: rgba(245, 158, 11, 0.14); color: #b45309; }
      .badge.hold { background: rgba(99, 112, 143, 0.16); color: #475467; }
      .badge.default { background: rgba(20, 93, 255, 0.12); color: #145dff; }

      .actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      .text-button {
        border: 0;
        background: transparent;
        padding: 0;
        color: var(--primary);
        font-size: 12px;
        font-weight: 900;
      }

      .text-button.danger {
        color: var(--danger);
      }

      .helper {
        margin-top: 12px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.7;
      }

      .detail-shell {
        display: grid;
        gap: 14px;
      }

      .detail-content {
        color: var(--text);
        font-size: 14px;
        line-height: 1.8;
      }

      .detail-content h1,
      .detail-content h2,
      .detail-content h3,
      .detail-content h4 {
        margin: 0 0 12px;
      }

      .detail-content p,
      .detail-content ul,
      .detail-content ol,
      .detail-content pre {
        margin: 0 0 12px;
      }

      .detail-content pre {
        white-space: pre-wrap;
        word-break: break-word;
        padding: 14px;
        border-radius: 14px;
        background: rgba(28, 36, 64, 0.05);
      }

      .detail-content img,
      .markdown-preview img {
        max-width: 100%;
        border-radius: 14px;
      }

      .markdown-editor {
        display: grid;
        gap: 12px;
      }

      .markdown-toolbar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }

      .toolbar-button {
        border: 1px solid rgba(28, 36, 64, 0.1);
        border-radius: 12px;
        padding: 9px 12px;
        background: rgba(28, 36, 64, 0.04);
        color: var(--text);
        font-size: 12px;
        font-weight: 800;
      }

      .toolbar-button.primary {
        background: var(--primary-soft);
        color: var(--primary);
      }

      .markdown-status {
        color: var(--muted);
        font-size: 12px;
        font-weight: 700;
      }

      .markdown-panes {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }

      .markdown-pane {
        display: grid;
        gap: 8px;
      }

      .markdown-pane-label {
        color: var(--muted);
        font-size: 12px;
        font-weight: 800;
      }

      .markdown-preview {
        min-height: 260px;
        padding: 14px;
        border-radius: 14px;
        border: 1px solid rgba(28, 36, 64, 0.12);
        background: rgba(28, 36, 64, 0.03);
        overflow: auto;
      }

      .empty, .error {
        padding: 20px 14px;
        text-align: center;
        border-radius: 16px;
        font-size: 13px;
      }

      .empty {
        background: rgba(28, 36, 64, 0.04);
        color: var(--muted);
      }

      .error {
        background: rgba(239, 68, 68, 0.1);
        color: #b42318;
      }

      .toast {
        position: fixed;
        right: 18px;
        bottom: 18px;
        max-width: 360px;
        padding: 14px 16px;
        border-radius: 18px;
        color: #fff;
        background: rgba(28, 36, 64, 0.92);
        box-shadow: 0 16px 40px rgba(28, 36, 64, 0.28);
        opacity: 0;
        transform: translateY(10px);
        pointer-events: none;
        transition: 180ms ease;
      }

      .toast.show {
        opacity: 1;
        transform: translateY(0);
      }

      @media (max-width: 1200px) {
        .grid, .hero {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 980px) {
        .workspace {
          grid-template-columns: 1fr;
        }

        .sidebar {
          border-right: 0;
          border-bottom: 1px solid var(--line);
        }
      }

      @media (max-width: 760px) {
        .page {
          width: min(100vw, calc(100vw - 16px));
          padding-top: 8px;
        }

        .hero, .content, .sidebar {
          padding: 16px;
        }

        .form-grid,
        .summary-grid,
        .status-grid,
        .markdown-panes {
          grid-template-columns: 1fr;
        }

        .table th:nth-child(n+4),
        .table td:nth-child(n+4) {
          display: none;
        }
      }
    </style>
  </head>
  <body>
    <div class="page">
      <section class="hero">
        <div>
          <p class="eyebrow">Cloudflare Python Worker</p>
          <h1>Agentic Product Studio 운영 화면</h1>
          <p>
            기존 Flask에서 사용하던 대시보드, 문서, WBS, 일정, 멤버 기능을 Worker 위에서 직접 다룰 수 있도록
            조회와 CRUD 중심 UI를 같은 배포 엔드포인트 안에 구성했습니다.
          </p>
          <div class="hero-actions">
            <button class="button" type="button" onclick="refreshAll()">전체 새로고침</button>
            <button class="button secondary" type="button" onclick="switchTab('dashboard')">대시보드 이동</button>
          </div>
        </div>
        <div class="status-grid">
          <div class="status-card"><span class="label">서비스 상태</span><div class="value" id="serviceStatus">확인 중</div></div>
          <div class="status-card"><span class="label">D1 연결</span><div class="value" id="dbStatus">확인 중</div></div>
          <div class="status-card"><span class="label">R2 연결</span><div class="value" id="r2Status">확인 중</div></div>
          <div class="status-card"><span class="label">최근 동기화</span><div class="value" id="syncStatus">-</div></div>
        </div>
      </section>

      <section class="workspace">
        <aside class="sidebar">
          <p class="sidebar-title">Workspace</p>
          <div class="nav">
            <button id="tabButton-dashboard" class="active" onclick="switchTab('dashboard')">대시보드</button>
            <button id="tabButton-documents" onclick="switchTab('documents')">문서</button>
            <button id="tabButton-wbs" onclick="switchTab('wbs')">WBS</button>
            <button id="tabButton-schedules" onclick="switchTab('schedules')">일정</button>
            <button id="tabButton-members" onclick="switchTab('members')">멤버</button>
          </div>
          <div class="sidebar-note">
            현재 화면은 Worker JSON API를 바로 사용하는 운영용 Web UI입니다.
            기존 Flask 템플릿과 완전히 같은 화면은 아니지만, 실제 데이터 조회와 주요 생성/수정/삭제 흐름을 여기서 처리하도록 확장합니다.
          </div>
        </aside>

        <main class="content">
          <section class="tab active" id="tab-dashboard">
            <div class="tab-header">
              <div>
                <h2>대시보드</h2>
                <p>Worker에 배포된 운영 데이터와 바인딩 상태를 한 눈에 확인합니다.</p>
              </div>
              <div class="meta-row">
                <div class="pill">Runtime: <span id="runtimeLabel">-</span></div>
                <div class="pill">D1 Colo: <span id="coloLabel">-</span></div>
                <div class="pill">기준일: <span id="dashboardDate">-</span></div>
              </div>
            </div>

            <div class="grid">
              <div class="panel">
                <div class="panel-head"><h3>요약 지표</h3><span>실시간 조회</span></div>
                <div class="panel-body">
                  <div class="summary-grid" id="summaryGrid"></div>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>예정 일정</h3><span>최대 6건</span></div>
                <div class="panel-body">
                  <div class="stack" id="upcomingSchedules"></div>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>최근 문서</h3><span id="recentDocumentsMeta">-</span></div>
                <div class="panel-body">
                  <div class="stack" id="recentDocuments"></div>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>최근 작업</h3><span id="recentTasksMeta">-</span></div>
                <div class="panel-body">
                  <div class="stack" id="recentTasks"></div>
                </div>
              </div>
            </div>
          </section>

          <section class="tab" id="tab-documents">
            <div class="tab-header">
              <div>
                <h2>문서</h2>
                <p>문서 목록 조회와 생성/수정/삭제를 Worker API 기준으로 처리합니다.</p>
              </div>
              <div class="meta-row">
                <div class="pill">전체 문서: <span id="documentsCount">0</span></div>
              </div>
            </div>

            <div class="grid">
              <div class="panel">
                <div class="panel-head"><h3>문서 폼</h3><span id="documentsFormState">새 문서</span></div>
                <div class="panel-body">
                  <form id="documentsForm">
                    <input type="hidden" id="document_id" />
                    <input type="hidden" id="document_asset_draft_key" />
                    <div class="form-grid">
                      <div class="field"><label for="document_title">제목</label><input id="document_title" required /></div>
                      <div class="field"><label for="document_doc_type">문서 유형</label><select id="document_doc_type"></select></div>
                      <div class="field"><label for="document_folder_id">폴더</label><select id="document_folder_id"></select></div>
                      <div class="field"><label for="document_new_folder_name">새 폴더명</label><input id="document_new_folder_name" placeholder="필요 시 새 폴더 생성" /></div>
                      <div class="field"><label for="document_author_id">작성자</label><select id="document_author_id"></select></div>
                      <div class="field"><label for="document_tags">태그</label><input id="document_tags" placeholder="쉼표로 구분" /></div>
                      <div class="field full"><label for="document_related_task_ids">연결 작업</label><select id="document_related_task_ids" multiple size="6"></select></div>
                      <div class="field full">
                        <label for="document_content">본문</label>
                        <div class="markdown-editor">
                          <div class="markdown-toolbar">
                            <button class="toolbar-button" type="button" onclick="insertDocumentMarkdown('# 제목')">H1</button>
                            <button class="toolbar-button" type="button" onclick="insertDocumentMarkdown('## 소제목')">H2</button>
                            <button class="toolbar-button" type="button" onclick="insertDocumentMarkdown('- 목록 항목')">List</button>
                            <button class="toolbar-button" type="button" onclick="insertDocumentMarkdown('**강조**')">Bold</button>
                            <button class="toolbar-button" type="button" onclick="insertDocumentMarkdown('`code`')">Code</button>
                            <button class="toolbar-button" type="button" onclick="insertDocumentMarkdown('```\ncode\n```')">Block</button>
                            <button class="toolbar-button primary" type="button" onclick="formatDocumentMarkdown()">코드 정리</button>
                            <button class="toolbar-button primary" type="button" onclick="triggerDocumentImageUpload()">이미지 업로드</button>
                            <span class="markdown-status" id="documentMarkdownStatus">미리보기 준비 중...</span>
                          </div>
                          <input id="document_image_input" type="file" accept="image/*" hidden />
                          <div class="markdown-panes">
                            <div class="markdown-pane">
                              <span class="markdown-pane-label">Editor</span>
                              <textarea id="document_content" placeholder="Markdown 본문 입력"></textarea>
                            </div>
                            <div class="markdown-pane">
                              <span class="markdown-pane-label">Preview</span>
                              <div id="document_preview" class="markdown-preview"></div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="field full">
                        <label class="checkbox"><input type="checkbox" id="document_is_hidden" /> 숨김 문서로 저장</label>
                      </div>
                    </div>
                    <div class="form-actions">
                      <button class="button" type="submit">저장</button>
                      <button class="button secondary" type="button" onclick="resetDocumentForm()">초기화</button>
                    </div>
                    <div class="helper">클립보드 붙여넣기, 드래그 앤 드롭, 업로드 버튼 모두 같은 Worker 이미지 업로드 API를 사용합니다.</div>
                  </form>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>문서 목록</h3><span>선택 시 폼에 채움</span></div>
                <div class="panel-body table-wrap">
                  <table class="table">
                    <thead><tr><th>제목</th><th>유형</th><th>작성자</th><th>작업</th></tr></thead>
                    <tbody id="documentsTable"></tbody>
                  </table>
                </div>
              </div>

              <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-head"><h3>문서 상세</h3><span id="documentsDetailMeta">문서를 선택하세요</span></div>
                <div class="panel-body">
                  <div id="documentsDetail" class="detail-shell">
                    <div class="empty">문서 목록에서 항목을 선택하면 본문과 연결 정보를 여기서 확인할 수 있습니다.</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="tab" id="tab-wbs">
            <div class="tab-header">
              <div>
                <h2>WBS</h2>
                <p>상태, 우선순위, 진행률, 문서 연결까지 Worker에서 직접 편집합니다.</p>
              </div>
              <div class="meta-row">
                <div class="pill">전체 작업: <span id="wbsCount">0</span></div>
              </div>
            </div>

            <div class="grid">
              <div class="panel">
                <div class="panel-head"><h3>WBS 폼</h3><span id="wbsFormState">새 작업</span></div>
                <div class="panel-body">
                  <form id="wbsForm">
                    <input type="hidden" id="wbs_id" />
                    <div class="form-grid">
                      <div class="field"><label for="wbs_parent_id">상위 작업</label><select id="wbs_parent_id"></select></div>
                      <div class="field"><label for="wbs_assignee_id">담당자</label><select id="wbs_assignee_id"></select></div>
                      <div class="field full"><label for="wbs_title">작업명</label><input id="wbs_title" required /></div>
                      <div class="field"><label for="wbs_platform">플랫폼</label><select id="wbs_platform"></select></div>
                      <div class="field"><label for="wbs_status">상태</label><select id="wbs_status"></select></div>
                      <div class="field"><label for="wbs_priority">우선순위</label><select id="wbs_priority"></select></div>
                      <div class="field"><label for="wbs_start_date">시작일</label><input id="wbs_start_date" type="date" /></div>
                      <div class="field"><label for="wbs_due_date">마감일</label><input id="wbs_due_date" type="date" /></div>
                      <div class="field"><label for="wbs_completed_date">완료일</label><input id="wbs_completed_date" type="date" /></div>
                      <div class="field"><label for="wbs_progress">진행률</label><input id="wbs_progress" type="number" min="0" max="100" value="0" /></div>
                      <div class="field full"><label for="wbs_document_ids">연결 문서</label><select id="wbs_document_ids" multiple size="6"></select></div>
                      <div class="field full"><label for="wbs_description">설명</label><textarea id="wbs_description"></textarea></div>
                      <div class="field full"><label for="wbs_notes">메모</label><textarea id="wbs_notes"></textarea></div>
                    </div>
                    <div class="form-actions">
                      <button class="button" type="submit">저장</button>
                      <button class="button secondary" type="button" onclick="resetWbsForm()">초기화</button>
                    </div>
                  </form>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>WBS 목록</h3><span>선택 시 폼에 채움</span></div>
                <div class="panel-body table-wrap">
                  <table class="table">
                    <thead><tr><th>작업명</th><th>상태</th><th>우선순위</th><th>작업</th></tr></thead>
                    <tbody id="wbsTable"></tbody>
                  </table>
                </div>
              </div>

              <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-head"><h3>WBS 상세</h3><span id="wbsDetailMeta">작업을 선택하세요</span></div>
                <div class="panel-body">
                  <div id="wbsDetail" class="detail-shell">
                    <div class="empty">작업 목록에서 항목을 선택하면 설명, 일정, 연결 문서를 여기서 확인할 수 있습니다.</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="tab" id="tab-schedules">
            <div class="tab-header">
              <div>
                <h2>일정</h2>
                <p>일정 유형, 담당자, WBS 연결 정보까지 Worker 화면에서 관리합니다.</p>
              </div>
              <div class="meta-row">
                <div class="pill">전체 일정: <span id="schedulesCount">0</span></div>
              </div>
            </div>

            <div class="grid">
              <div class="panel">
                <div class="panel-head"><h3>일정 폼</h3><span id="schedulesFormState">새 일정</span></div>
                <div class="panel-body">
                  <form id="schedulesForm">
                    <input type="hidden" id="schedule_id" />
                    <div class="form-grid">
                      <div class="field full"><label for="schedule_title">제목</label><input id="schedule_title" required /></div>
                      <div class="field"><label for="schedule_type">일정 유형</label><select id="schedule_type"></select></div>
                      <div class="field"><label for="schedule_assignee_id">담당자</label><select id="schedule_assignee_id"></select></div>
                      <div class="field"><label for="schedule_wbs_task_id">연결 작업</label><select id="schedule_wbs_task_id"></select></div>
                      <div class="field"><label for="schedule_start_date">시작일</label><input id="schedule_start_date" type="date" required /></div>
                      <div class="field"><label for="schedule_end_date">종료일</label><input id="schedule_end_date" type="date" required /></div>
                      <div class="field full"><label for="schedule_description">설명</label><textarea id="schedule_description"></textarea></div>
                    </div>
                    <div class="form-actions">
                      <button class="button" type="submit">저장</button>
                      <button class="button secondary" type="button" onclick="resetScheduleForm()">초기화</button>
                    </div>
                  </form>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>일정 목록</h3><span>선택 시 폼에 채움</span></div>
                <div class="panel-body table-wrap">
                  <table class="table">
                    <thead><tr><th>제목</th><th>유형</th><th>담당자</th><th>작업</th></tr></thead>
                    <tbody id="schedulesTable"></tbody>
                  </table>
                </div>
              </div>

              <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-head"><h3>일정 상세</h3><span id="schedulesDetailMeta">일정을 선택하세요</span></div>
                <div class="panel-body">
                  <div id="schedulesDetail" class="detail-shell">
                    <div class="empty">일정 목록에서 항목을 선택하면 설명과 연결 작업 정보를 여기서 확인할 수 있습니다.</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="tab" id="tab-members">
            <div class="tab-header">
              <div>
                <h2>멤버</h2>
                <p>멤버 기본 정보와 활성 상태를 Worker 화면에서 직접 관리합니다.</p>
              </div>
              <div class="meta-row">
                <div class="pill">전체 멤버: <span id="membersCount">0</span></div>
              </div>
            </div>

            <div class="grid">
              <div class="panel">
                <div class="panel-head"><h3>멤버 폼</h3><span id="membersFormState">새 멤버</span></div>
                <div class="panel-body">
                  <form id="membersForm">
                    <input type="hidden" id="member_id" />
                    <div class="form-grid">
                      <div class="field"><label for="member_name">이름</label><input id="member_name" required /></div>
                      <div class="field"><label for="member_role">역할</label><input id="member_role" /></div>
                      <div class="field"><label for="member_part">파트</label><input id="member_part" /></div>
                      <div class="field"><label for="member_contact">연락처</label><input id="member_contact" /></div>
                      <div class="field full">
                        <label class="checkbox"><input type="checkbox" id="member_is_active" checked /> 활성 멤버로 유지</label>
                      </div>
                    </div>
                    <div class="form-actions">
                      <button class="button" type="submit">저장</button>
                      <button class="button secondary" type="button" onclick="resetMemberForm()">초기화</button>
                    </div>
                  </form>
                </div>
              </div>

              <div class="panel">
                <div class="panel-head"><h3>멤버 목록</h3><span>선택 시 폼에 채움</span></div>
                <div class="panel-body table-wrap">
                  <table class="table">
                    <thead><tr><th>이름</th><th>역할</th><th>파트</th><th>작업</th></tr></thead>
                    <tbody id="membersTable"></tbody>
                  </table>
                </div>
              </div>

              <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-head"><h3>멤버 상세</h3><span id="membersDetailMeta">멤버를 선택하세요</span></div>
                <div class="panel-body">
                  <div id="membersDetail" class="detail-shell">
                    <div class="empty">멤버 목록에서 항목을 선택하면 담당 작업과 문서 작성 이력을 여기서 확인할 수 있습니다.</div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </main>
      </section>
    </div>

    <div class="toast" id="toast"></div>

    <script>
      const DOC_TYPES = ["기획서", "기술문서", "회의록", "참고자료", "API 문서", "기타"];
      const WBS_STATUSES = ["예정", "진행중", "검토중", "완료", "보류"];
      const WBS_PRIORITIES = ["낮음", "보통", "높음", "긴급"];
      const WBS_PLATFORMS = ["Agentic Product Studio", "외부 에셋 카탈로그(게임 제작)"];
      const SCHEDULE_TYPES = ["개발", "회의", "테스트", "배포", "리뷰", "기타"];

      const state = {
        activeTab: "dashboard",
        commonOptions: null,
        runtime: null,
        health: null,
        dashboard: null,
        documents: null,
        schedules: null,
        members: null,
        wbs: null,
        folders: null
      };

      let documentPreviewTimer = null;

      function escapeHtml(value) {
        return String(value ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }

      function badgeClass(status) {
        if (status === "완료") return "done";
        if (status === "진행중" || status === "검토중") return "progress";
        if (status === "보류") return "hold";
        return "default";
      }

      function selectedValues(selectId) {
        return Array.from(document.getElementById(selectId).selectedOptions)
          .map((option) => Number(option.value))
          .filter((value) => Number.isInteger(value));
      }

      function fillSelect(selectId, items, valueKey, labelBuilder, includeEmpty = true) {
        const select = document.getElementById(selectId);
        const options = [];
        if (includeEmpty) {
          options.push('<option value="">선택 안 함</option>');
        }
        for (const item of items) {
          options.push(`<option value="${escapeHtml(item[valueKey])}">${escapeHtml(labelBuilder(item))}</option>`);
        }
        select.innerHTML = options.join("");
      }

      function fillMultiSelect(selectId, items, valueKey, labelBuilder) {
        const select = document.getElementById(selectId);
        select.innerHTML = items.map((item) => (
          `<option value="${escapeHtml(item[valueKey])}">${escapeHtml(labelBuilder(item))}</option>`
        )).join("");
      }

      function setMultiSelectValues(selectId, values) {
        const selected = new Set((values || []).map(Number));
        const select = document.getElementById(selectId);
        for (const option of select.options) {
          option.selected = selected.has(Number(option.value));
        }
      }

      function setSelectValue(selectId, value) {
        document.getElementById(selectId).value = value ?? "";
      }

      function formatDateTime(value) {
        if (!value) return "-";
        const normalized = String(value).replace(" ", "T");
        const date = new Date(normalized);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString("ko-KR");
      }

      function showToast(message, isError = false) {
        const toast = document.getElementById("toast");
        toast.textContent = message;
        toast.style.background = isError ? "rgba(180, 35, 24, 0.92)" : "rgba(28, 36, 64, 0.92)";
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 2400);
      }

      function setDocumentMarkdownStatus(message) {
        document.getElementById("documentMarkdownStatus").textContent = message;
      }

      function ensureDocumentDraftKey() {
        const input = document.getElementById("document_asset_draft_key");
        if (!input.value) {
          input.value = (globalThis.crypto && crypto.randomUUID)
            ? crypto.randomUUID().replaceAll("-", "")
            : `draft-${Date.now()}`;
        }
        return input.value;
      }

      function insertDocumentMarkdown(snippet) {
        const textarea = document.getElementById("document_content");
        const start = textarea.selectionStart ?? textarea.value.length;
        const end = textarea.selectionEnd ?? textarea.value.length;
        const selected = textarea.value.slice(start, end);
        const text = snippet.includes("{selection}")
          ? snippet.replace("{selection}", selected || "text")
          : snippet;
        textarea.setRangeText(text, start, end, "end");
        textarea.focus();
        scheduleDocumentPreview();
      }

      async function syncDocumentPreview() {
        const content = document.getElementById("document_content").value;
        const body = new URLSearchParams();
        body.set("content", content);
        setDocumentMarkdownStatus("미리보기 반영 중...");
        try {
          const response = await fetch("/api/documents/preview-markdown", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
            body: body.toString()
          });
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.error || "Preview failed");
          }
          document.getElementById("document_preview").innerHTML = payload.html || '<div class="empty">미리보기가 없습니다.</div>';
          setDocumentMarkdownStatus("미리보기 동기화됨");
        } catch (error) {
          setDocumentMarkdownStatus(error.message || "미리보기 실패");
        }
      }

      function scheduleDocumentPreview() {
        if (documentPreviewTimer) {
          clearTimeout(documentPreviewTimer);
        }
        documentPreviewTimer = setTimeout(syncDocumentPreview, 180);
      }

      async function formatDocumentMarkdown() {
        const textarea = document.getElementById("document_content");
        const body = new URLSearchParams();
        body.set("content", textarea.value);
        setDocumentMarkdownStatus("코드 블록 정리 중...");
        try {
          const response = await fetch("/api/documents/format-markdown", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
            body: body.toString()
          });
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.error || "Format failed");
          }
          textarea.value = payload.content || textarea.value;
          scheduleDocumentPreview();
          setDocumentMarkdownStatus("코드 블록 정리 완료");
        } catch (error) {
          setDocumentMarkdownStatus(error.message || "코드 정리 실패");
        }
      }

      function triggerDocumentImageUpload() {
        ensureDocumentDraftKey();
        document.getElementById("document_image_input").click();
      }

      async function uploadDocumentImage(file) {
        if (!file) return;
        const form = new FormData();
        const documentId = document.getElementById("document_id").value;
        form.set("image", file);
        form.set("alt", file.name.replace(/\\.[^.]+$/, ""));
        form.set("draft_key", ensureDocumentDraftKey());
        if (documentId) {
          form.set("document_id", documentId);
        }

        setDocumentMarkdownStatus("이미지 업로드 중...");
        try {
          const response = await fetch("/api/documents/upload-image", {
            method: "POST",
            body: form
          });
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.error || "Upload failed");
          }
          if (payload.draft_key) {
            document.getElementById("document_asset_draft_key").value = payload.draft_key;
          }
          insertDocumentMarkdown(`\n${payload.markdown}\n`);
          setDocumentMarkdownStatus("이미지 업로드 완료");
          showToast("이미지를 업로드했습니다.");
        } catch (error) {
          setDocumentMarkdownStatus(error.message || "이미지 업로드 실패");
          showToast(error.message || "이미지 업로드 실패", true);
        } finally {
          document.getElementById("document_image_input").value = "";
        }
      }

      async function fetchJson(url, options = {}) {
        const response = await fetch(url, {
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            ...(options.headers || {})
          },
          ...options
        });

        if (!response.ok) {
          let payload = "";
          try {
            const data = await response.json();
            payload = data.error || data.detail || JSON.stringify(data);
          } catch {
            payload = await response.text();
          }
          throw new Error(payload || `${response.status} ${response.statusText}`);
        }

        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          return await response.json();
        }
        return await response.text();
      }

      function switchTab(tabName) {
        state.activeTab = tabName;
        document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
        document.querySelectorAll(".nav button").forEach((button) => button.classList.remove("active"));
        document.getElementById(`tab-${tabName}`).classList.add("active");
        document.getElementById(`tabButton-${tabName}`).classList.add("active");
      }

      async function refreshRuntime() {
        const [health, runtime] = await Promise.all([
          fetchJson("/health"),
          fetchJson("/api/runtime-summary")
        ]);
        state.health = health;
        state.runtime = runtime;
        document.getElementById("serviceStatus").textContent = health.ok ? "정상" : "오류";
        document.getElementById("dbStatus").textContent = health.has_db_binding ? "연결됨" : "없음";
        document.getElementById("r2Status").textContent = health.has_image_bucket_binding ? "연결됨" : "없음";
        document.getElementById("syncStatus").textContent = new Date().toLocaleTimeString("ko-KR");
        document.getElementById("runtimeLabel").textContent = runtime.worker_runtime || "-";
        document.getElementById("coloLabel").textContent = runtime?.d1?.table_list?.meta?.served_by_colo || "-";
      }

      async function refreshDashboard() {
        const dashboard = await fetchJson("/api/dashboard");
        state.dashboard = dashboard;
        document.getElementById("dashboardDate").textContent = dashboard.today || "-";
        const summary = dashboard.summary || {};
        document.getElementById("summaryGrid").innerHTML = `
          <div class="summary-box"><span class="label">전체 작업</span><div class="value">${summary.total_tasks ?? 0}</div></div>
          <div class="summary-box"><span class="label">진행 중</span><div class="value">${summary.in_progress_tasks ?? 0}</div></div>
          <div class="summary-box"><span class="label">완료</span><div class="value">${summary.completed_tasks ?? 0}</div></div>
          <div class="summary-box"><span class="label">지연</span><div class="value">${summary.delayed_tasks ?? 0}</div></div>
        `;
        renderFeed("upcomingSchedules", dashboard.upcoming_schedules || [], (item) => `
          <div class="feed-item">
            <strong>${escapeHtml(item.title)}</strong>
            <div class="meta">${escapeHtml(item.schedule_type || "-")} · ${escapeHtml(item.assignee_name || "-")}</div>
            <div class="meta">${escapeHtml(item.start_date || "-")} ~ ${escapeHtml(item.end_date || "-")}</div>
          </div>
        `, "예정된 일정이 없습니다.");
        document.getElementById("recentDocumentsMeta").textContent = `${(dashboard.recent_documents || []).length}건`;
        renderFeed("recentDocuments", dashboard.recent_documents || [], (item) => `
          <div class="feed-item">
            <strong>${escapeHtml(item.title)}</strong>
            <div class="meta">${escapeHtml(item.doc_type || "-")} · ${escapeHtml(item.author_name || "-")}</div>
            <div class="meta">${escapeHtml(formatDateTime(item.updated_at))}</div>
          </div>
        `, "최근 문서가 없습니다.");
        document.getElementById("recentTasksMeta").textContent = `${(dashboard.recent_tasks || []).length}건`;
        renderFeed("recentTasks", dashboard.recent_tasks || [], (item) => `
          <div class="feed-item">
            <strong>${escapeHtml(item.title)}</strong>
            <div class="meta"><span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status || "-")}</span> ${escapeHtml(item.priority || "-")}</div>
            <div class="meta">${escapeHtml(item.assignee_name || "-")} · ${escapeHtml(formatDateTime(item.updated_at))}</div>
          </div>
        `, "최근 작업이 없습니다.");
      }

      function renderFeed(targetId, items, renderer, emptyMessage) {
        const target = document.getElementById(targetId);
        if (!items || items.length === 0) {
          target.innerHTML = `<div class="empty">${escapeHtml(emptyMessage)}</div>`;
          return;
        }
        target.innerHTML = items.map(renderer).join("");
      }

      async function refreshCommonOptions() {
        const [commonOptions, folders] = await Promise.all([
          fetchJson("/api/common/options"),
          fetchJson("/api/document-folders")
        ]);
        state.commonOptions = commonOptions;
        state.folders = folders;

        fillSelect("document_author_id", commonOptions.active_members || [], "id", (item) => item.name);
        fillSelect("schedule_assignee_id", commonOptions.active_members || [], "id", (item) => item.name);
        fillSelect("wbs_assignee_id", commonOptions.active_members || [], "id", (item) => item.name);

        fillSelect("schedule_wbs_task_id", commonOptions.task_link_options || [], "id", (item) => item.title);
        fillSelect("wbs_parent_id", commonOptions.parent_task_options || [], "id", (item) => item.title);

        fillMultiSelect("document_related_task_ids", commonOptions.task_link_options || [], "id", (item) => item.title);
        fillMultiSelect("wbs_document_ids", commonOptions.document_link_options || [], "id", (item) => item.title);

        fillSelect("document_folder_id", folders.folders || [], "id", (item) => `${item.doc_type} / ${item.name}`);

        populateStaticSelect("document_doc_type", DOC_TYPES, true);
        populateStaticSelect("wbs_status", WBS_STATUSES, false);
        populateStaticSelect("wbs_priority", WBS_PRIORITIES, false);
        populateStaticSelect("wbs_platform", WBS_PLATFORMS, false);
        populateStaticSelect("schedule_type", SCHEDULE_TYPES, false);
      }

      function populateStaticSelect(selectId, values, includeEmpty) {
        const select = document.getElementById(selectId);
        const options = [];
        if (includeEmpty) options.push('<option value="">선택 안 함</option>');
        for (const value of values) {
          options.push(`<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`);
        }
        select.innerHTML = options.join("");
      }

      async function refreshDocuments() {
        const documents = await fetchJson("/api/documents?limit=100");
        state.documents = documents;
        document.getElementById("documentsCount").textContent = String(documents.total_count ?? 0);
        const rows = documents.documents || [];
        const table = document.getElementById("documentsTable");
        if (rows.length === 0) {
          table.innerHTML = `<tr><td colspan="4"><div class="empty">문서가 없습니다.</div></td></tr>`;
          return;
        }
        table.innerHTML = rows.map((item) => `
          <tr>
            <td><div class="row-title">${escapeHtml(item.title)}</div><div class="helper">${escapeHtml(item.folder_name || "-")}</div></td>
            <td>${escapeHtml(item.doc_type || "-")}</td>
            <td>${escapeHtml(item.author_name || "-")}</td>
            <td>
              <div class="actions">
                <button class="text-button" type="button" onclick="viewDocument(${item.id})">보기</button>
                <button class="text-button" type="button" onclick="editDocument(${item.id})">수정</button>
                <button class="text-button danger" type="button" onclick="deleteDocument(${item.id})">삭제</button>
              </div>
            </td>
          </tr>
        `).join("");
      }

      async function viewDocument(documentId) {
        const detail = await fetchJson(`/api/documents/${documentId}`);
        document.getElementById("documentsDetailMeta").textContent = `${detail.document.doc_type || "-"} · ${detail.document.author_name || "-"} · ${formatDateTime(detail.document.updated_at)}`;
        const tags = (detail.tags || []).length
          ? detail.tags.map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`).join("")
          : '<span class="muted-text">태그 없음</span>';
        const assets = (detail.assets || []).length
          ? detail.assets.map((asset) => `
              <div class="feed-item">
                <strong><a href="${escapeHtml(asset.url)}" target="_blank" rel="noreferrer">${escapeHtml(asset.original_filename)}</a></strong>
                <div class="meta">${escapeHtml(asset.content_type || "image/*")} · ${escapeHtml(asset.size)} bytes</div>
                <div class="actions" style="margin-top:8px;">
                  <button class="text-button danger" type="button" onclick="deleteDocumentAsset(${detail.document.id}, ${asset.id})">이미지 삭제</button>
                </div>
              </div>
            `).join("")
          : '<div class="empty">첨부 이미지가 없습니다.</div>';
        const relatedTasks = (detail.related_tasks || []).length
          ? detail.related_tasks.map((task) => `
              <div class="feed-item">
                <strong>${escapeHtml(task.title)}</strong>
                <div class="meta">${escapeHtml(task.status || "-")} · ${escapeHtml(task.priority || "-")}</div>
              </div>
            `).join("")
          : '<div class="empty">연결된 WBS 작업이 없습니다.</div>';

        document.getElementById("documentsDetail").innerHTML = `
          <div>
            <h3 style="margin:0 0 10px;">${escapeHtml(detail.document.title)}</h3>
            <div class="meta-row">${tags}</div>
          </div>
          <div class="detail-content">${detail.rendered_content || '<div class="empty">본문이 없습니다.</div>'}</div>
          <div class="grid">
            <div class="panel">
              <div class="panel-head"><h3>연결 작업</h3><span>${(detail.related_tasks || []).length}건</span></div>
              <div class="panel-body"><div class="stack">${relatedTasks}</div></div>
            </div>
            <div class="panel">
              <div class="panel-head"><h3>이미지 자산</h3><span>${(detail.assets || []).length}건</span></div>
              <div class="panel-body"><div class="stack">${assets}</div></div>
            </div>
          </div>
        `;
        switchTab("documents");
      }

      async function deleteDocumentAsset(documentId, assetId) {
        if (!confirm(`이미지 자산 #${assetId}를 삭제할까요?`)) return;
        await fetchJson(`/api/documents/${documentId}/assets/${assetId}`, { method: "DELETE" });
        showToast("문서 이미지를 삭제했습니다.");
        await viewDocument(documentId);
      }

      async function editDocument(documentId) {
        const detail = await fetchJson(`/api/documents/${documentId}`);
        const doc = detail.document;
        document.getElementById("document_id").value = doc.id;
        document.getElementById("document_asset_draft_key").value = "";
        document.getElementById("document_title").value = doc.title || "";
        setSelectValue("document_doc_type", doc.doc_type || "");
        setSelectValue("document_folder_id", doc.folder_id || "");
        document.getElementById("document_new_folder_name").value = "";
        setSelectValue("document_author_id", doc.author_id || "");
        document.getElementById("document_tags").value = (detail.tags || []).join(", ");
        document.getElementById("document_content").value = doc.content || "";
        document.getElementById("document_is_hidden").checked = Boolean(doc.is_hidden);
        setMultiSelectValues("document_related_task_ids", (detail.related_tasks || []).map((item) => item.id));
        document.getElementById("documentsFormState").textContent = `문서 #${doc.id} 수정`;
        await syncDocumentPreview();
        switchTab("documents");
      }

      function resetDocumentForm() {
        document.getElementById("documentsForm").reset();
        document.getElementById("document_id").value = "";
        document.getElementById("document_asset_draft_key").value = "";
        document.getElementById("documentsFormState").textContent = "새 문서";
        setMultiSelectValues("document_related_task_ids", []);
        document.getElementById("document_preview").innerHTML = '<div class="empty">미리보기가 없습니다.</div>';
        setDocumentMarkdownStatus("미리보기 준비 중...");
        ensureDocumentDraftKey();
      }

      async function saveDocument(event) {
        event.preventDefault();
        const id = document.getElementById("document_id").value;
        const payload = {
          title: document.getElementById("document_title").value.trim(),
          doc_type: document.getElementById("document_doc_type").value || DOC_TYPES[DOC_TYPES.length - 1],
          folder_id: document.getElementById("document_folder_id").value ? Number(document.getElementById("document_folder_id").value) : null,
          new_folder_name: document.getElementById("document_new_folder_name").value.trim(),
          asset_draft_key: document.getElementById("document_asset_draft_key").value.trim(),
          content: document.getElementById("document_content").value,
          author_id: document.getElementById("document_author_id").value ? Number(document.getElementById("document_author_id").value) : null,
          tags: document.getElementById("document_tags").value.trim(),
          is_hidden: document.getElementById("document_is_hidden").checked ? 1 : 0,
          related_task_ids: selectedValues("document_related_task_ids")
        };

        if (id) {
          await fetchJson(`/api/documents/${id}`, { method: "PUT", body: JSON.stringify(payload) });
          showToast("문서를 수정했습니다.");
        } else {
          await fetchJson("/api/documents", { method: "POST", body: JSON.stringify(payload) });
          showToast("문서를 생성했습니다.");
        }

        resetDocumentForm();
        await refreshCommonOptions();
        await refreshDocuments();
        await refreshDashboard();
      }

      async function deleteDocument(documentId) {
        if (!confirm(`문서 #${documentId}를 삭제할까요?`)) return;
        await fetchJson(`/api/documents/${documentId}`, { method: "DELETE" });
        showToast("문서를 삭제했습니다.");
        resetDocumentForm();
        await refreshCommonOptions();
        await refreshDocuments();
        await refreshDashboard();
      }

      async function refreshWbs() {
        const wbs = await fetchJson("/api/wbs");
        state.wbs = wbs;
        document.getElementById("wbsCount").textContent = String((wbs.tasks || []).length);
        const rows = wbs.tasks || [];
        const table = document.getElementById("wbsTable");
        if (rows.length === 0) {
          table.innerHTML = `<tr><td colspan="4"><div class="empty">작업이 없습니다.</div></td></tr>`;
          return;
        }
        table.innerHTML = rows.map((item) => `
          <tr>
            <td><div class="row-title">${escapeHtml(item.title)}</div><div class="helper">${escapeHtml(item.parent_title || item.platform || "-")}</div></td>
            <td><span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status || "-")}</span></td>
            <td>${escapeHtml(item.priority || "-")}</td>
            <td>
              <div class="actions">
                <button class="text-button" type="button" onclick="viewWbs(${item.id})">보기</button>
                <button class="text-button" type="button" onclick="editWbs(${item.id})">수정</button>
                <button class="text-button danger" type="button" onclick="deleteWbs(${item.id})">삭제</button>
              </div>
            </td>
          </tr>
        `).join("");
      }

      async function viewWbs(taskId) {
        const detail = await fetchJson(`/api/wbs/${taskId}`);
        const task = detail.task;
        document.getElementById("wbsDetailMeta").textContent = `${escapeHtml(task.status || "-")} · ${escapeHtml(task.priority || "-")} · ${escapeHtml(task.assignee_name || "-")}`;
        const linkedDocuments = (detail.linked_documents || []).length
          ? detail.linked_documents.map((doc) => `
              <div class="feed-item">
                <strong>${escapeHtml(doc.title)}</strong>
                <div class="meta">${escapeHtml(doc.doc_type || "-")} · ${escapeHtml(formatDateTime(doc.updated_at))}</div>
              </div>
            `).join("")
          : '<div class="empty">연결된 문서가 없습니다.</div>';
        document.getElementById("wbsDetail").innerHTML = `
          <div class="panel">
            <div class="panel-body">
              <div class="stack">
                <div><strong>${escapeHtml(task.title)}</strong></div>
                <div class="meta">상위 작업: ${escapeHtml(task.parent_title || "-")}</div>
                <div class="meta">플랫폼: ${escapeHtml(task.platform || "-")} · 진행률: ${escapeHtml(task.progress ?? 0)}%</div>
                <div class="meta">기간: ${escapeHtml(task.start_date || "-")} ~ ${escapeHtml(task.due_date || "-")}</div>
                <div class="detail-content">${escapeHtml(task.description || "설명이 없습니다.")}</div>
                <div class="detail-content">${escapeHtml(task.notes || "메모가 없습니다.")}</div>
              </div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-head"><h3>연결 문서</h3><span>${(detail.linked_documents || []).length}건</span></div>
            <div class="panel-body"><div class="stack">${linkedDocuments}</div></div>
          </div>
        `;
        switchTab("wbs");
      }

      async function editWbs(taskId) {
        const detail = await fetchJson(`/api/wbs/${taskId}`);
        const row = detail.task;
        document.getElementById("wbs_id").value = row.id;
        setSelectValue("wbs_parent_id", row.parent_id || "");
        document.getElementById("wbs_title").value = row.title || "";
        document.getElementById("wbs_description").value = row.description || "";
        setSelectValue("wbs_assignee_id", row.assignee_id || "");
        setSelectValue("wbs_platform", row.platform || WBS_PLATFORMS[0]);
        setSelectValue("wbs_status", row.status || WBS_STATUSES[0]);
        setSelectValue("wbs_priority", row.priority || WBS_PRIORITIES[1]);
        document.getElementById("wbs_start_date").value = row.start_date || "";
        document.getElementById("wbs_due_date").value = row.due_date || "";
        document.getElementById("wbs_completed_date").value = row.completed_date || "";
        document.getElementById("wbs_progress").value = row.progress ?? 0;
        document.getElementById("wbs_notes").value = row.notes || "";
        const options = await fetchJson(`/api/common/options?exclude_task_id=${taskId}`);
        fillSelect("wbs_parent_id", options.parent_task_options || [], "id", (item) => item.title);
        setSelectValue("wbs_parent_id", row.parent_id || "");
        setMultiSelectValues("wbs_document_ids", detail.document_ids || []);
        document.getElementById("wbsFormState").textContent = `작업 #${taskId} 수정`;
        switchTab("wbs");
      }

      function resetWbsForm() {
        document.getElementById("wbsForm").reset();
        document.getElementById("wbs_id").value = "";
        document.getElementById("wbsFormState").textContent = "새 작업";
        setMultiSelectValues("wbs_document_ids", []);
      }

      async function saveWbs(event) {
        event.preventDefault();
        const id = document.getElementById("wbs_id").value;
        const payload = {
          parent_id: document.getElementById("wbs_parent_id").value ? Number(document.getElementById("wbs_parent_id").value) : null,
          title: document.getElementById("wbs_title").value.trim(),
          description: document.getElementById("wbs_description").value,
          assignee_id: document.getElementById("wbs_assignee_id").value ? Number(document.getElementById("wbs_assignee_id").value) : null,
          platform: document.getElementById("wbs_platform").value || WBS_PLATFORMS[0],
          status: document.getElementById("wbs_status").value || WBS_STATUSES[0],
          priority: document.getElementById("wbs_priority").value || WBS_PRIORITIES[1],
          start_date: document.getElementById("wbs_start_date").value || null,
          due_date: document.getElementById("wbs_due_date").value || null,
          completed_date: document.getElementById("wbs_completed_date").value || null,
          progress: Number(document.getElementById("wbs_progress").value || 0),
          notes: document.getElementById("wbs_notes").value,
          document_ids: selectedValues("wbs_document_ids")
        };

        if (id) {
          await fetchJson(`/api/wbs/${id}`, { method: "PUT", body: JSON.stringify(payload) });
          showToast("WBS 작업을 수정했습니다.");
        } else {
          await fetchJson("/api/wbs", { method: "POST", body: JSON.stringify(payload) });
          showToast("WBS 작업을 생성했습니다.");
        }

        resetWbsForm();
        await refreshCommonOptions();
        await refreshWbs();
        await refreshDashboard();
      }

      async function deleteWbs(taskId) {
        if (!confirm(`작업 #${taskId}를 삭제할까요?`)) return;
        await fetchJson(`/api/wbs/${taskId}`, { method: "DELETE" });
        showToast("WBS 작업을 삭제했습니다.");
        resetWbsForm();
        await refreshCommonOptions();
        await refreshWbs();
        await refreshDashboard();
      }

      async function refreshSchedules() {
        const schedules = await fetchJson("/api/schedules");
        state.schedules = schedules;
        document.getElementById("schedulesCount").textContent = String((schedules.schedules || []).length);
        const rows = schedules.schedules || [];
        const table = document.getElementById("schedulesTable");
        if (rows.length === 0) {
          table.innerHTML = `<tr><td colspan="4"><div class="empty">일정이 없습니다.</div></td></tr>`;
          return;
        }
        table.innerHTML = rows.map((item) => `
          <tr>
            <td><div class="row-title">${escapeHtml(item.title)}</div><div class="helper">${escapeHtml(item.start_date || "-")} ~ ${escapeHtml(item.end_date || "-")}</div></td>
            <td>${escapeHtml(item.schedule_type || "-")}</td>
            <td>${escapeHtml(item.assignee_name || "-")}</td>
            <td>
              <div class="actions">
                <button class="text-button" type="button" onclick="viewSchedule(${item.id})">보기</button>
                <button class="text-button" type="button" onclick="editSchedule(${item.id})">수정</button>
                <button class="text-button danger" type="button" onclick="deleteSchedule(${item.id})">삭제</button>
              </div>
            </td>
          </tr>
        `).join("");
      }

      async function viewSchedule(scheduleId) {
        const detail = await fetchJson(`/api/schedules/${scheduleId}`);
        document.getElementById("schedulesDetailMeta").textContent = `${escapeHtml(detail.schedule_type || "-")} · ${escapeHtml(detail.assignee_name || "-")}`;
        document.getElementById("schedulesDetail").innerHTML = `
          <div class="panel">
            <div class="panel-body">
              <div class="stack">
                <div><strong>${escapeHtml(detail.title)}</strong></div>
                <div class="meta">담당자: ${escapeHtml(detail.assignee_name || "-")}</div>
                <div class="meta">연결 작업: ${escapeHtml(detail.task_title || "-")}</div>
                <div class="meta">기간: ${escapeHtml(detail.start_date || "-")} ~ ${escapeHtml(detail.end_date || "-")}</div>
                <div class="detail-content">${escapeHtml(detail.description || "설명이 없습니다.")}</div>
              </div>
            </div>
          </div>
        `;
        switchTab("schedules");
      }

      async function editSchedule(scheduleId) {
        const detail = await fetchJson(`/api/schedules/${scheduleId}`);
        document.getElementById("schedule_id").value = detail.id;
        document.getElementById("schedule_title").value = detail.title || "";
        setSelectValue("schedule_type", detail.schedule_type || SCHEDULE_TYPES[0]);
        setSelectValue("schedule_assignee_id", detail.assignee_id || "");
        setSelectValue("schedule_wbs_task_id", detail.wbs_task_id || "");
        document.getElementById("schedule_start_date").value = detail.start_date || "";
        document.getElementById("schedule_end_date").value = detail.end_date || "";
        document.getElementById("schedule_description").value = detail.description || "";
        document.getElementById("schedulesFormState").textContent = `일정 #${scheduleId} 수정`;
        switchTab("schedules");
      }

      function resetScheduleForm() {
        document.getElementById("schedulesForm").reset();
        document.getElementById("schedule_id").value = "";
        document.getElementById("schedulesFormState").textContent = "새 일정";
      }

      async function saveSchedule(event) {
        event.preventDefault();
        const id = document.getElementById("schedule_id").value;
        const payload = {
          title: document.getElementById("schedule_title").value.trim(),
          description: document.getElementById("schedule_description").value,
          start_date: document.getElementById("schedule_start_date").value,
          end_date: document.getElementById("schedule_end_date").value,
          assignee_id: document.getElementById("schedule_assignee_id").value ? Number(document.getElementById("schedule_assignee_id").value) : null,
          wbs_task_id: document.getElementById("schedule_wbs_task_id").value ? Number(document.getElementById("schedule_wbs_task_id").value) : null,
          schedule_type: document.getElementById("schedule_type").value || SCHEDULE_TYPES[0]
        };

        if (id) {
          await fetchJson(`/api/schedules/${id}`, { method: "PUT", body: JSON.stringify(payload) });
          showToast("일정을 수정했습니다.");
        } else {
          await fetchJson("/api/schedules", { method: "POST", body: JSON.stringify(payload) });
          showToast("일정을 생성했습니다.");
        }

        resetScheduleForm();
        await refreshSchedules();
        await refreshDashboard();
      }

      async function deleteSchedule(scheduleId) {
        if (!confirm(`일정 #${scheduleId}를 삭제할까요?`)) return;
        await fetchJson(`/api/schedules/${scheduleId}`, { method: "DELETE" });
        showToast("일정을 삭제했습니다.");
        resetScheduleForm();
        await refreshSchedules();
        await refreshDashboard();
      }

      async function refreshMembers() {
        const members = await fetchJson("/api/members");
        state.members = members;
        document.getElementById("membersCount").textContent = String((members.members || []).length);
        const rows = members.members || [];
        const table = document.getElementById("membersTable");
        if (rows.length === 0) {
          table.innerHTML = `<tr><td colspan="4"><div class="empty">멤버가 없습니다.</div></td></tr>`;
          return;
        }
        table.innerHTML = rows.map((item) => `
          <tr>
            <td><div class="row-title">${escapeHtml(item.name)}</div><div class="helper">${item.is_active ? "활성" : "비활성"}</div></td>
            <td>${escapeHtml(item.role || "-")}</td>
            <td>${escapeHtml(item.part || "-")}</td>
            <td>
              <div class="actions">
                <button class="text-button" type="button" onclick="viewMember(${item.id})">보기</button>
                <button class="text-button" type="button" onclick="editMember(${item.id})">수정</button>
                <button class="text-button danger" type="button" onclick="deleteMember(${item.id})">삭제</button>
              </div>
            </td>
          </tr>
        `).join("");
      }

      async function viewMember(memberId) {
        const detail = await fetchJson(`/api/members/${memberId}`);
        const member = detail.member;
        document.getElementById("membersDetailMeta").textContent = `${escapeHtml(member.role || "-")} · ${escapeHtml(member.part || "-")}`;
        const tasks = (detail.assigned_tasks || []).length
          ? detail.assigned_tasks.map((task) => `
              <div class="feed-item">
                <strong>${escapeHtml(task.title)}</strong>
                <div class="meta">${escapeHtml(task.status || "-")} · ${escapeHtml(task.priority || "-")} · ${escapeHtml(task.progress ?? 0)}%</div>
              </div>
            `).join("")
          : '<div class="empty">담당 작업이 없습니다.</div>';
        const docs = (detail.authored_documents || []).length
          ? detail.authored_documents.map((doc) => `
              <div class="feed-item">
                <strong>${escapeHtml(doc.title)}</strong>
                <div class="meta">${escapeHtml(doc.doc_type || "-")} · ${escapeHtml(formatDateTime(doc.updated_at))}</div>
              </div>
            `).join("")
          : '<div class="empty">작성 문서가 없습니다.</div>';
        document.getElementById("membersDetail").innerHTML = `
          <div class="grid">
            <div class="panel">
              <div class="panel-body">
                <div class="stack">
                  <div><strong>${escapeHtml(member.name)}</strong></div>
                  <div class="meta">연락처: ${escapeHtml(member.contact || "-")}</div>
                  <div class="meta">상태: ${member.is_active ? "활성" : "비활성"}</div>
                  <div class="meta">작업 ${escapeHtml(member.task_count ?? 0)}건 · 일정 ${escapeHtml(member.schedule_count ?? 0)}건</div>
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="panel-head"><h3>작성 문서</h3><span>${(detail.authored_documents || []).length}건</span></div>
              <div class="panel-body"><div class="stack">${docs}</div></div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-head"><h3>담당 작업</h3><span>${(detail.assigned_tasks || []).length}건</span></div>
            <div class="panel-body"><div class="stack">${tasks}</div></div>
          </div>
        `;
        switchTab("members");
      }

      async function editMember(memberId) {
        const detail = await fetchJson(`/api/members/${memberId}`);
        const member = detail.member;
        document.getElementById("member_id").value = member.id;
        document.getElementById("member_name").value = member.name || "";
        document.getElementById("member_role").value = member.role || "";
        document.getElementById("member_part").value = member.part || "";
        document.getElementById("member_contact").value = member.contact || "";
        document.getElementById("member_is_active").checked = Boolean(member.is_active);
        document.getElementById("membersFormState").textContent = `멤버 #${memberId} 수정`;
        switchTab("members");
      }

      function resetMemberForm() {
        document.getElementById("membersForm").reset();
        document.getElementById("member_id").value = "";
        document.getElementById("member_is_active").checked = true;
        document.getElementById("membersFormState").textContent = "새 멤버";
      }

      async function saveMember(event) {
        event.preventDefault();
        const id = document.getElementById("member_id").value;
        const payload = {
          name: document.getElementById("member_name").value.trim(),
          role: document.getElementById("member_role").value.trim(),
          part: document.getElementById("member_part").value.trim(),
          contact: document.getElementById("member_contact").value.trim(),
          is_active: document.getElementById("member_is_active").checked ? 1 : 0
        };

        if (id) {
          await fetchJson(`/api/members/${id}`, { method: "PUT", body: JSON.stringify(payload) });
          showToast("멤버를 수정했습니다.");
        } else {
          await fetchJson("/api/members", { method: "POST", body: JSON.stringify(payload) });
          showToast("멤버를 생성했습니다.");
        }

        resetMemberForm();
        await refreshMembers();
        await refreshCommonOptions();
      }

      async function deleteMember(memberId) {
        if (!confirm(`멤버 #${memberId}를 삭제할까요?`)) return;
        await fetchJson(`/api/members/${memberId}`, { method: "DELETE" });
        showToast("멤버를 삭제했습니다.");
        resetMemberForm();
        await refreshMembers();
        await refreshCommonOptions();
      }

      async function refreshAll() {
        try {
          await refreshRuntime();
          await refreshCommonOptions();
          await Promise.all([
            refreshDashboard(),
            refreshDocuments(),
            refreshWbs(),
            refreshSchedules(),
            refreshMembers()
          ]);
        } catch (error) {
          showToast(error.message, true);
        }
      }

      document.getElementById("documentsForm").addEventListener("submit", saveDocument);
      document.getElementById("wbsForm").addEventListener("submit", saveWbs);
      document.getElementById("schedulesForm").addEventListener("submit", saveSchedule);
      document.getElementById("membersForm").addEventListener("submit", saveMember);
      document.getElementById("document_content").addEventListener("input", scheduleDocumentPreview);
      document.getElementById("document_image_input").addEventListener("change", async (event) => {
        const [file] = Array.from(event.target.files || []);
        await uploadDocumentImage(file);
      });
      document.getElementById("document_content").addEventListener("paste", async (event) => {
        const items = Array.from(event.clipboardData?.items || []);
        const imageItem = items.find((item) => item.type?.startsWith("image/"));
        if (!imageItem) return;
        const file = imageItem.getAsFile();
        if (!file) return;
        event.preventDefault();
        await uploadDocumentImage(file);
      });
      document.getElementById("document_content").addEventListener("dragover", (event) => {
        event.preventDefault();
      });
      document.getElementById("document_content").addEventListener("drop", async (event) => {
        event.preventDefault();
        const [file] = Array.from(event.dataTransfer?.files || []);
        await uploadDocumentImage(file);
      });

      resetDocumentForm();
      refreshAll();
    </script>
  </body>
</html>
"""
