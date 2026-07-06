from __future__ import annotations


APP_CSS = r"""
:root {
  --bg: #eef3fb;
  --sidebar: #172338;
  --sidebar-line: rgba(255,255,255,0.08);
  --panel: #ffffff;
  --panel-soft: #f7faff;
  --text: #172033;
  --muted: #62708c;
  --line: #dbe3f0;
  --primary: #1f63ff;
  --primary-strong: #114eda;
  --success: #0f9f66;
  --warning: #d28719;
  --danger: #d14848;
  --radius: 20px;
  --shadow: 0 18px 40px rgba(17, 24, 39, 0.08);
}

* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body {
  background:
    radial-gradient(circle at top left, rgba(31, 99, 255, 0.08), transparent 28%),
    linear-gradient(180deg, #f7fbff 0%, var(--bg) 100%);
  color: var(--text);
  font-family: "Segoe UI", "Noto Sans KR", sans-serif;
}
a { color: inherit; text-decoration: none; }
button, input, select, textarea { font: inherit; }
button { cursor: pointer; }

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 264px minmax(0, 1fr);
}

.sidebar {
  background: var(--sidebar);
  color: #d9e4f7;
  padding: 24px 20px;
  border-right: 1px solid var(--sidebar-line);
}

.sidebar__eyebrow,
.topbar__eyebrow,
.section-eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.sidebar__eyebrow { color: #8facd4; }
.sidebar__title {
  display: inline-block;
  color: #ffffff;
  font-size: 1.8rem;
  font-weight: 900;
  line-height: 1.15;
}
.sidebar__caption {
  margin: 16px 0 0;
  color: #9bb0cd;
  line-height: 1.7;
}
.sidebar__nav {
  display: grid;
  gap: 10px;
  margin-top: 28px;
}
.nav-link {
  display: block;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid transparent;
  color: #d7e3f5;
  font-weight: 700;
}
.nav-link:hover,
.nav-link.is-active {
  background: rgba(255,255,255,0.06);
  border-color: rgba(111, 147, 201, 0.35);
  color: #ffffff;
}
.sidebar__note {
  margin-top: 24px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(111, 147, 201, 0.22);
  background: rgba(255,255,255,0.03);
}
.sidebar__note strong {
  display: block;
  margin-bottom: 6px;
  color: #ffffff;
}
.sidebar__note p {
  margin: 0;
  color: #9bb0cd;
  line-height: 1.7;
}

.main-shell {
  min-width: 0;
  padding: 28px 28px 42px;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.topbar__eyebrow { color: var(--muted); }
.topbar__title {
  margin: 0;
  font-size: clamp(2rem, 3vw, 2.9rem);
  line-height: 1.08;
  letter-spacing: -0.04em;
}
.topbar__subtitle {
  margin: 12px 0 0;
  color: var(--muted);
  line-height: 1.7;
}
.topbar__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.page-content {
  display: grid;
  gap: 18px;
  margin-top: 24px;
}

.panel {
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(14px);
  border: 1px solid var(--line);
  border-radius: 22px;
  box-shadow: var(--shadow);
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 20px 22px 0;
}
.panel-head h2,
.panel-head h3 {
  margin: 0;
}
.panel-head p {
  margin: 8px 0 0;
  color: var(--muted);
}
.panel-body {
  padding: 20px 22px 22px;
}

.button {
  border: 1px solid rgba(23, 32, 51, 0.12);
  background: #ffffff;
  color: var(--text);
  min-height: 42px;
  padding: 0 16px;
  border-radius: 14px;
  font-weight: 800;
}
.button.primary {
  border-color: var(--primary-strong);
  background: linear-gradient(135deg, var(--primary), #6997ff);
  color: #fff;
}
.button.danger {
  border-color: rgba(209, 72, 72, 0.24);
  background: #fff4f4;
  color: var(--danger);
}
.button.ghost {
  background: rgba(23, 32, 51, 0.04);
}
.button.sm {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 12px;
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}
.stat-card {
  padding: 18px;
  border-radius: 18px;
  background: var(--panel-soft);
  border: 1px solid rgba(23, 32, 51, 0.06);
}
.stat-card .label {
  display: block;
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 8px;
}
.stat-card .value {
  font-size: 2rem;
  font-weight: 900;
}

.split-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 18px;
}

.docs-editor-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 18px;
}

.stack {
  display: grid;
  gap: 12px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.field {
  display: grid;
  gap: 7px;
}
.field.full {
  grid-column: 1 / -1;
}
.field label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}
.field input,
.field select,
.field textarea {
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(23, 32, 51, 0.13);
  background: #fff;
  padding: 12px 14px;
}
.field textarea {
  resize: vertical;
  min-height: 120px;
}
.helper {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.toolbar .spacer {
  flex: 1 1 auto;
}

.markdown-panes {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
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
.markdown-editor {
  min-height: 520px;
  font-family: Consolas, "Courier New", monospace;
}
.markdown-preview {
  min-height: 520px;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(23, 32, 51, 0.08);
  background: rgba(23, 32, 51, 0.03);
  overflow: auto;
}
.markdown-preview h1,
.markdown-preview h2,
.markdown-preview h3,
.markdown-preview h4,
.detail-content h1,
.detail-content h2,
.detail-content h3,
.detail-content h4 {
  margin: 0 0 14px;
}
.markdown-preview p,
.markdown-preview ul,
.markdown-preview ol,
.markdown-preview pre,
.detail-content p,
.detail-content ul,
.detail-content ol,
.detail-content pre {
  margin: 0 0 14px;
}
.markdown-preview pre,
.detail-content pre {
  padding: 14px;
  border-radius: 14px;
  background: rgba(23, 32, 51, 0.06);
  white-space: pre-wrap;
}
.markdown-preview img,
.detail-content img {
  max-width: 100%;
  border-radius: 14px;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  background: rgba(23, 32, 51, 0.05);
  color: var(--muted);
}
.badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}
.badge.done { background: rgba(15, 159, 102, 0.12); color: #08764b; }
.badge.progress { background: rgba(210, 135, 25, 0.14); color: #9b620f; }
.badge.hold { background: rgba(98, 112, 140, 0.16); color: #4b5974; }
.badge.default { background: rgba(31, 99, 255, 0.1); color: var(--primary); }
.badge.high { background: rgba(255, 231, 205, 1); color: #9e5b16; }
.badge.urgent { background: rgba(255, 225, 225, 1); color: #a12626; }
.badge.low { background: rgba(235, 241, 249, 1); color: #4f617f; }

.table-wrap {
  overflow: auto;
}
.table {
  width: 100%;
  border-collapse: collapse;
}
.table th,
.table td {
  padding: 14px 12px;
  border-top: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
.table thead th {
  border-top: 0;
  color: var(--muted);
  font-size: 12px;
}
.row-title {
  font-weight: 800;
}
.row-sub {
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.text-button {
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--primary);
  font-size: 12px;
  font-weight: 900;
}
.text-button.danger { color: var(--danger); }

.empty {
  padding: 18px;
  border-radius: 16px;
  background: rgba(23, 32, 51, 0.04);
  color: var(--muted);
  text-align: center;
}

.feed-item {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(23, 32, 51, 0.08);
  background: rgba(23, 32, 51, 0.03);
}
.feed-item strong {
  display: block;
  margin-bottom: 6px;
}
.feed-item .meta {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.detail-shell {
  display: grid;
  gap: 16px;
}

.detail-content {
  line-height: 1.8;
}

.progress {
  display: grid;
  gap: 6px;
}
.progress-bar {
  width: 140px;
  height: 8px;
  border-radius: 999px;
  background: rgba(23, 32, 51, 0.08);
  overflow: hidden;
}
.progress-bar > span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--primary), #7ca4ff);
}

.toast {
  position: fixed;
  right: 18px;
  bottom: 18px;
  max-width: 360px;
  padding: 14px 16px;
  border-radius: 18px;
  color: #fff;
  background: rgba(23, 32, 51, 0.94);
  box-shadow: 0 16px 40px rgba(23, 32, 51, 0.22);
  opacity: 0;
  transform: translateY(8px);
  transition: 180ms ease;
  pointer-events: none;
}
.toast.show {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 1200px) {
  .split-grid,
  .docs-editor-grid,
  .stats-grid,
  .markdown-panes {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }
  .sidebar {
    border-right: 0;
    border-bottom: 1px solid var(--sidebar-line);
  }
  .field-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .main-shell {
    padding: 18px 14px 28px;
  }
  .topbar {
    flex-direction: column;
    align-items: stretch;
  }
  .panel-head,
  .panel-body {
    padding-left: 16px;
    padding-right: 16px;
  }
  .table th:nth-child(n+5),
  .table td:nth-child(n+5) {
    display: none;
  }
}
"""


APP_JS = r"""
const $body = document.body;

function $(id) {
  return document.getElementById(id);
}

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

function priorityClass(priority) {
  if (priority === "긴급") return "urgent";
  if (priority === "높음") return "high";
  if (priority === "낮음") return "low";
  return "default";
}

function formatDateTime(value) {
  if (!value) return "-";
  const normalized = String(value).replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ko-KR");
}

function showToast(message, isError = false) {
  const toast = $("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.style.background = isError ? "rgba(177,40,40,.94)" : "rgba(23,32,51,.94)";
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message = isJson
      ? payload.error || payload.detail || JSON.stringify(payload)
      : payload;
    throw new Error(message || `${response.status} ${response.statusText}`);
  }

  return payload;
}

function fillSelect(selectId, items, valueKey, labelBuilder, includeEmpty = true, emptyLabel = "선택") {
  const select = $(selectId);
  if (!select) return;
  const options = [];
  if (includeEmpty) {
    options.push(`<option value="">${escapeHtml(emptyLabel)}</option>`);
  }
  for (const item of items || []) {
    const optionValue = valueKey == null ? item : item[valueKey];
    options.push(`<option value="${escapeHtml(optionValue)}">${escapeHtml(labelBuilder(item))}</option>`);
  }
  select.innerHTML = options.join("");
}

function fillMultiSelect(selectId, items, valueKey, labelBuilder) {
  const select = $(selectId);
  if (!select) return;
  select.innerHTML = (items || []).map((item) =>
    `<option value="${escapeHtml(item[valueKey])}">${escapeHtml(labelBuilder(item))}</option>`
  ).join("");
}

function setSelectValue(selectId, value) {
  const target = $(selectId);
  if (target) target.value = value ?? "";
}

function selectedValues(selectId) {
  const select = $(selectId);
  if (!select) return [];
  return Array.from(select.selectedOptions || [])
    .map((option) => Number(option.value))
    .filter((value) => Number.isInteger(value));
}

function setMultiSelectValues(selectId, values) {
  const select = $(selectId);
  if (!select) return;
  const selected = new Set((values || []).map(Number));
  for (const option of select.options) {
    option.selected = selected.has(Number(option.value));
  }
}

async function initDashboardPage() {
  const [runtime, dashboard] = await Promise.all([
    fetchJson("/api/runtime-summary"),
    fetchJson("/api/dashboard")
  ]);

  const summary = dashboard.summary || {};
  $("dashboardStats").innerHTML = [
    ["전체 작업", summary.total_tasks ?? 0],
    ["진행 중", summary.in_progress_tasks ?? 0],
    ["완료", summary.completed_tasks ?? 0],
    ["지연", summary.delayed_tasks ?? 0],
  ].map(([label, value]) => `
    <div class="stat-card">
      <span class="label">${label}</span>
      <div class="value">${escapeHtml(value)}</div>
    </div>
  `).join("");

  $("dashboardUpcoming").innerHTML = (dashboard.upcoming_schedules || []).length
    ? dashboard.upcoming_schedules.map((item) => `
        <div class="feed-item">
          <strong>${escapeHtml(item.title)}</strong>
          <div class="meta">${escapeHtml(item.schedule_type || "-")} · ${escapeHtml(item.assignee_name || "-")} · ${escapeHtml(item.start_date || "-")} ~ ${escapeHtml(item.end_date || "-")}</div>
        </div>
      `).join("")
    : `<div class="empty">예정 일정이 없습니다.</div>`;

  $("dashboardRecentDocs").innerHTML = (dashboard.recent_documents || []).length
    ? dashboard.recent_documents.map((item) => `
        <div class="feed-item">
          <strong><a href="/documents/${item.id}">${escapeHtml(item.title)}</a></strong>
          <div class="meta">${escapeHtml(item.doc_type || "-")} · ${escapeHtml(item.author_name || "-")} · ${escapeHtml(formatDateTime(item.updated_at))}</div>
        </div>
      `).join("")
    : `<div class="empty">최근 문서가 없습니다.</div>`;

  $("dashboardRecentTasks").innerHTML = (dashboard.recent_tasks || []).length
    ? dashboard.recent_tasks.map((item) => `
        <div class="feed-item">
          <strong>${escapeHtml(item.title)}</strong>
          <div class="meta">${escapeHtml(item.status || "-")} · ${escapeHtml(item.priority || "-")} · ${escapeHtml(item.assignee_name || "-")}</div>
        </div>
      `).join("")
    : `<div class="empty">최근 작업이 없습니다.</div>`;

  $("runtimePills").innerHTML = `
    <span class="pill">Runtime: ${escapeHtml(runtime.worker_runtime || "-")}</span>
    <span class="pill">D1: ${runtime.bindings?.db ? "연결됨" : "미연결"}</span>
    <span class="pill">R2: ${runtime.bindings?.document_images ? "연결됨" : "미연결"}</span>
    <span class="pill">기준일: ${escapeHtml(dashboard.today || "-")}</span>
  `;
}

async function initDocumentsListPage() {
  const common = await fetchJson("/api/common/options");
  const folders = await fetchJson("/api/document-folders");
  fillSelect("docsFilterType", (window.WORKER_CONSTANTS || {}).documentTypes || [], null, (item) => item, true, "전체");
  fillSelect("docsFilterFolder", folders.folders || [], "id", (item) => `${item.doc_type} / ${item.name}`, true, "전체");

  async function loadDocuments() {
    const params = new URLSearchParams();
    if ($("docsFilterQuery").value.trim()) params.set("q", $("docsFilterQuery").value.trim());
    if ($("docsFilterType").value) params.set("doc_type", $("docsFilterType").value);
    if ($("docsFilterFolder").value) params.set("folder_id", $("docsFilterFolder").value);
    const data = await fetchJson(`/api/documents?limit=100&${params.toString()}`);
    $("docsCount").textContent = String(data.total_count ?? 0);
    $("docsTable").innerHTML = (data.documents || []).length
      ? data.documents.map((item) => `
          <tr>
            <td>
              <div class="row-title"><a href="/documents/${item.id}">${escapeHtml(item.title)}</a></div>
              <div class="row-sub">${escapeHtml(item.folder_name || "미지정")}</div>
            </td>
            <td>${escapeHtml(item.doc_type || "-")}</td>
            <td>${escapeHtml(item.author_name || "-")}</td>
            <td>${escapeHtml(formatDateTime(item.updated_at))}</td>
            <td>
              <div class="actions">
                <a class="button sm ghost" href="/documents/${item.id}">보기</a>
                <a class="button sm ghost" href="/documents/${item.id}/edit">수정</a>
                <button class="button sm danger" type="button" data-delete-doc="${item.id}">삭제</button>
              </div>
            </td>
          </tr>
        `).join("")
      : `<tr><td colspan="5"><div class="empty">조건에 맞는 문서가 없습니다.</div></td></tr>`;
  }

  $("docsFilterForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await loadDocuments();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  $("docsTable").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-delete-doc]");
    if (!button) return;
    const documentId = button.getAttribute("data-delete-doc");
    if (!confirm(`문서 #${documentId}를 삭제할까요?`)) return;
    try {
      await fetchJson(`/api/documents/${documentId}`, { method: "DELETE" });
      showToast("문서를 삭제했습니다.");
      await loadDocuments();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  await loadDocuments();
}

function ensureDraftKey() {
  const target = $("documentAssetDraftKey");
  if (!target.value) {
    target.value = (globalThis.crypto && crypto.randomUUID)
      ? crypto.randomUUID().replaceAll("-", "")
      : `draft-${Date.now()}`;
  }
  return target.value;
}

let documentPreviewTimer = null;

function insertEditorSnippet(snippet) {
  const textarea = $("documentContent");
  const start = textarea.selectionStart ?? textarea.value.length;
  const end = textarea.selectionEnd ?? textarea.value.length;
  const selected = textarea.value.slice(start, end);
  const text = snippet.includes("{selection}") ? snippet.replace("{selection}", selected || "text") : snippet;
  textarea.setRangeText(text, start, end, "end");
  textarea.focus();
  scheduleDocumentPreview();
}

function setEditorStatus(message) {
  const target = $("documentEditorStatus");
  if (target) target.textContent = message;
}

async function syncDocumentPreview() {
  const body = new URLSearchParams();
  body.set("content", $("documentContent").value);
  setEditorStatus("미리보기 반영 중...");
  try {
    const response = await fetch("/api/documents/preview-markdown", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
      body: body.toString()
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Preview failed");
    $("documentPreview").innerHTML = payload.html || `<div class="empty">미리보기가 없습니다.</div>`;
    setEditorStatus("미리보기 동기화됨");
  } catch (error) {
    setEditorStatus(error.message || "미리보기 실패");
  }
}

function scheduleDocumentPreview() {
  if (documentPreviewTimer) clearTimeout(documentPreviewTimer);
  documentPreviewTimer = setTimeout(syncDocumentPreview, 180);
}

async function formatDocumentMarkdown() {
  const body = new URLSearchParams();
  body.set("content", $("documentContent").value);
  setEditorStatus("코드 블록 정리 중...");
  try {
    const response = await fetch("/api/documents/format-markdown", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
      body: body.toString()
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Format failed");
    $("documentContent").value = payload.content || $("documentContent").value;
    scheduleDocumentPreview();
    setEditorStatus("코드 블록 정리 완료");
  } catch (error) {
    setEditorStatus(error.message || "코드 정리 실패");
  }
}

async function uploadDocumentImage(file) {
  if (!file) return;
  const body = new FormData();
  const documentId = $("documentFormPage").dataset.documentId || "";
  body.set("image", file);
  body.set("alt", file.name.replace(/\.[^.]+$/, ""));
  body.set("draft_key", ensureDraftKey());
  if (documentId) body.set("document_id", documentId);
  setEditorStatus("이미지 업로드 중...");
  try {
    const response = await fetch("/api/documents/upload-image", { method: "POST", body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Upload failed");
    if (payload.draft_key) $("documentAssetDraftKey").value = payload.draft_key;
    insertEditorSnippet(`\n${payload.markdown}\n`);
    showToast("이미지를 업로드했습니다.");
    setEditorStatus("이미지 업로드 완료");
  } catch (error) {
    showToast(error.message, true);
    setEditorStatus(error.message || "이미지 업로드 실패");
  } finally {
    $("documentImageInput").value = "";
  }
}

async function initDocumentFormPage() {
  const page = $("documentFormPage");
  const documentId = page.dataset.documentId || "";
  const constants = window.WORKER_CONSTANTS || {};
  const [commonOptions, folders] = await Promise.all([
    fetchJson("/api/common/options"),
    fetchJson("/api/document-folders")
  ]);

  fillSelect("documentDocType", constants.documentTypes || [], null, (item) => item, false);
  fillSelect("documentFolderId", folders.folders || [], "id", (item) => `${item.doc_type} / ${item.name}`, true, "미지정");
  fillSelect("documentAuthorId", commonOptions.active_members || [], "id", (item) => item.name, true, "미지정");
  fillMultiSelect("documentRelatedTaskIds", commonOptions.task_link_options || [], "id", (item) => `#${item.id} ${item.title}`);

  if (documentId) {
    const detail = await fetchJson(`/api/documents/${documentId}`);
    const doc = detail.document;
    $("documentTitle").value = doc.title || "";
    setSelectValue("documentDocType", doc.doc_type || "");
    setSelectValue("documentFolderId", doc.folder_id || "");
    setSelectValue("documentAuthorId", doc.author_id || "");
    $("documentTags").value = (detail.tags || []).join(", ");
    $("documentContent").value = doc.content || "";
    $("documentHidden").checked = Boolean(doc.is_hidden);
    setMultiSelectValues("documentRelatedTaskIds", (detail.related_tasks || []).map((item) => item.id));
  } else {
    ensureDraftKey();
  }

  $("documentToolbar").addEventListener("click", async (event) => {
    const insert = event.target.closest("[data-insert]");
    if (insert) {
      insertEditorSnippet(insert.getAttribute("data-insert"));
      return;
    }
    if (event.target.closest("[data-format-markdown]")) {
      await formatDocumentMarkdown();
      return;
    }
    if (event.target.closest("[data-upload-image]")) {
      ensureDraftKey();
      $("documentImageInput").click();
    }
  });

  $("documentImageInput").addEventListener("change", async (event) => {
    const [file] = Array.from(event.target.files || []);
    await uploadDocumentImage(file);
  });

  $("documentContent").addEventListener("input", scheduleDocumentPreview);
  $("documentContent").addEventListener("paste", async (event) => {
    const items = Array.from(event.clipboardData?.items || []);
    const imageItem = items.find((item) => item.type?.startsWith("image/"));
    if (!imageItem) return;
    const file = imageItem.getAsFile();
    if (!file) return;
    event.preventDefault();
    await uploadDocumentImage(file);
  });
  $("documentContent").addEventListener("dragover", (event) => event.preventDefault());
  $("documentContent").addEventListener("drop", async (event) => {
    event.preventDefault();
    const [file] = Array.from(event.dataTransfer?.files || []);
    await uploadDocumentImage(file);
  });

  $("documentForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      title: $("documentTitle").value.trim(),
      doc_type: $("documentDocType").value,
      folder_id: $("documentFolderId").value ? Number($("documentFolderId").value) : null,
      new_folder_name: $("documentNewFolderName").value.trim(),
      asset_draft_key: $("documentAssetDraftKey").value.trim(),
      content: $("documentContent").value,
      author_id: $("documentAuthorId").value ? Number($("documentAuthorId").value) : null,
      tags: $("documentTags").value.trim(),
      is_hidden: $("documentHidden").checked ? 1 : 0,
      related_task_ids: selectedValues("documentRelatedTaskIds"),
    };

    try {
      const endpoint = documentId ? `/api/documents/${documentId}` : "/api/documents";
      const method = documentId ? "PUT" : "POST";
      const result = await fetchJson(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const nextId = result.document_id || documentId;
      showToast(documentId ? "문서를 수정했습니다." : "문서를 생성했습니다.");
      location.href = `/documents/${nextId}`;
    } catch (error) {
      showToast(error.message, true);
    }
  });

  await syncDocumentPreview();
}

async function initDocumentDetailPage() {
  const documentId = $("documentDetailPage").dataset.documentId;
  const detail = await fetchJson(`/api/documents/${documentId}`);
  $("documentDetailTitle").textContent = detail.document.title || "";
  $("documentDetailMeta").textContent = `${detail.document.doc_type || "-"} · ${detail.document.author_name || "-"} · ${formatDateTime(detail.document.updated_at)}`;
  $("documentDetailBody").innerHTML = detail.rendered_content || `<div class="empty">본문이 없습니다.</div>`;
  $("documentDetailTags").innerHTML = (detail.tags || []).length
    ? detail.tags.map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`).join("")
    : `<span class="helper">태그 없음</span>`;
  $("documentDetailTasks").innerHTML = (detail.related_tasks || []).length
    ? detail.related_tasks.map((task) => `
        <div class="feed-item">
          <strong>${escapeHtml(task.title)}</strong>
          <div class="meta">${escapeHtml(task.status || "-")} · ${escapeHtml(task.priority || "-")}</div>
        </div>
      `).join("")
    : `<div class="empty">연결된 작업이 없습니다.</div>`;
  $("documentDetailAssets").innerHTML = (detail.assets || []).length
    ? detail.assets.map((asset) => `
        <div class="feed-item">
          <strong><a href="${escapeHtml(asset.url)}" target="_blank" rel="noreferrer">${escapeHtml(asset.original_filename)}</a></strong>
          <div class="meta">${escapeHtml(asset.content_type || "image/*")} · ${escapeHtml(asset.size)} bytes</div>
          <div class="actions" style="margin-top:8px;">
            <button class="button sm danger" type="button" data-delete-asset="${asset.id}">이미지 삭제</button>
          </div>
        </div>
      `).join("")
    : `<div class="empty">첨부 이미지가 없습니다.</div>`;

  $("documentDetailAssets").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-delete-asset]");
    if (!button) return;
    const assetId = button.getAttribute("data-delete-asset");
    if (!confirm(`이미지 자산 #${assetId}를 삭제할까요?`)) return;
    try {
      await fetchJson(`/api/documents/${documentId}/assets/${assetId}`, { method: "DELETE" });
      showToast("이미지를 삭제했습니다.");
      await initDocumentDetailPage();
    } catch (error) {
      showToast(error.message, true);
    }
  }, { once: true });
}

async function initWbsPage() {
  const constants = window.WORKER_CONSTANTS || {};
  const common = await fetchJson("/api/common/options");
  fillSelect("wbsFilterStatus", constants.taskStatuses || [], null, (item) => item, true, "전체");
  fillSelect("wbsFilterPriority", constants.taskPriorities || [], null, (item) => item, true, "전체");
  fillSelect("wbsFilterPlatform", constants.platforms || [], null, (item) => item, true, "전체");
  fillSelect("wbsFilterAssigneeId", common.active_members || [], "id", (item) => item.name, true, "전체");

  fillSelect("wbsParentId", common.parent_task_options || [], "id", (item) => `#${item.id} ${item.title}`, true, "없음");
  fillSelect("wbsAssigneeId", common.active_members || [], "id", (item) => item.name, true, "미지정");
  fillSelect("wbsPlatform", constants.platforms || [], null, (item) => item, false);
  fillSelect("wbsStatus", constants.taskStatuses || [], null, (item) => item, false);
  fillSelect("wbsPriority", constants.taskPriorities || [], null, (item) => item, false);
  fillMultiSelect("wbsDocumentIds", common.document_link_options || [], "id", (item) => item.title);

  async function loadWbs() {
    const params = new URLSearchParams();
    ["Status", "Priority", "Platform", "AssigneeId"].forEach((suffix) => {
      const value = $(`wbsFilter${suffix}`).value;
      if (value) {
        const map = { Status: "status", Priority: "priority", Platform: "platform", AssigneeId: "assignee_id" };
        params.set(map[suffix], value);
      }
    });
    const data = await fetchJson(`/api/wbs?${params.toString()}`);
    $("wbsCount").textContent = String((data.tasks || []).length);
    $("wbsTable").innerHTML = (data.tasks || []).length
      ? data.tasks.map((item) => `
          <tr>
            <td>
              <div class="row-title">${escapeHtml(item.title)}</div>
              <div class="row-sub">${escapeHtml(item.parent_title || item.platform || "-")}</div>
            </td>
            <td><span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status || "-")}</span></td>
            <td><span class="badge ${priorityClass(item.priority)}">${escapeHtml(item.priority || "-")}</span></td>
            <td>
              <div class="progress">
                <div class="progress-bar"><span style="width:${Number(item.progress || 0)}%"></span></div>
                <div class="helper">${escapeHtml(item.progress ?? 0)}%</div>
              </div>
            </td>
            <td>
              <div class="actions">
                <button class="button sm ghost" type="button" data-edit-wbs="${item.id}">수정</button>
                <button class="button sm danger" type="button" data-delete-wbs="${item.id}">삭제</button>
              </div>
            </td>
          </tr>
        `).join("")
      : `<tr><td colspan="5"><div class="empty">조건에 맞는 작업이 없습니다.</div></td></tr>`;
  }

  function resetWbsForm() {
    $("wbsForm").reset();
    $("wbsId").value = "";
    setMultiSelectValues("wbsDocumentIds", []);
    $("wbsFormTitle").textContent = "새 작업";
  }

  $("wbsFilterForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadWbs();
  });

  $("wbsResetButton").addEventListener("click", resetWbsForm);

  $("wbsTable").addEventListener("click", async (event) => {
    const edit = event.target.closest("[data-edit-wbs]");
    const del = event.target.closest("[data-delete-wbs]");
    if (edit) {
      const id = edit.getAttribute("data-edit-wbs");
      const detail = await fetchJson(`/api/wbs/${id}`);
      const row = detail.task;
      $("wbsId").value = row.id;
      setSelectValue("wbsParentId", row.parent_id || "");
      $("wbsTitle").value = row.title || "";
      $("wbsDescription").value = row.description || "";
      setSelectValue("wbsAssigneeId", row.assignee_id || "");
      setSelectValue("wbsPlatform", row.platform || (constants.platforms || [])[0] || "");
      setSelectValue("wbsStatus", row.status || (constants.taskStatuses || [])[0] || "");
      setSelectValue("wbsPriority", row.priority || (constants.taskPriorities || [])[1] || "");
      $("wbsStartDate").value = row.start_date || "";
      $("wbsDueDate").value = row.due_date || "";
      $("wbsCompletedDate").value = row.completed_date || "";
      $("wbsProgress").value = row.progress ?? 0;
      $("wbsNotes").value = row.notes || "";
      setMultiSelectValues("wbsDocumentIds", detail.document_ids || []);
      $("wbsFormTitle").textContent = `작업 #${id} 수정`;
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (del) {
      const id = del.getAttribute("data-delete-wbs");
      if (!confirm(`작업 #${id}를 삭제할까요?`)) return;
      await fetchJson(`/api/wbs/${id}`, { method: "DELETE" });
      showToast("작업을 삭제했습니다.");
      resetWbsForm();
      await loadWbs();
    }
  });

  $("wbsForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = $("wbsId").value;
    const payload = {
      parent_id: $("wbsParentId").value ? Number($("wbsParentId").value) : null,
      title: $("wbsTitle").value.trim(),
      description: $("wbsDescription").value,
      assignee_id: $("wbsAssigneeId").value ? Number($("wbsAssigneeId").value) : null,
      platform: $("wbsPlatform").value,
      status: $("wbsStatus").value,
      priority: $("wbsPriority").value,
      start_date: $("wbsStartDate").value || null,
      due_date: $("wbsDueDate").value || null,
      completed_date: $("wbsCompletedDate").value || null,
      progress: Number($("wbsProgress").value || 0),
      notes: $("wbsNotes").value,
      document_ids: selectedValues("wbsDocumentIds"),
    };
    const endpoint = id ? `/api/wbs/${id}` : "/api/wbs";
    const method = id ? "PUT" : "POST";
    await fetchJson(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(id ? "작업을 수정했습니다." : "작업을 생성했습니다.");
    resetWbsForm();
    await loadWbs();
  });

  resetWbsForm();
  await loadWbs();
}

async function initSchedulesPage() {
  const constants = window.WORKER_CONSTANTS || {};
  const common = await fetchJson("/api/common/options");
  fillSelect("scheduleAssigneeId", common.active_members || [], "id", (item) => item.name, true, "미지정");
  fillSelect("scheduleWbsTaskId", common.task_link_options || [], "id", (item) => item.title, true, "미지정");
  fillSelect("scheduleType", constants.scheduleTypes || [], null, (item) => item, false);

  async function loadSchedules() {
    const data = await fetchJson("/api/schedules");
    $("schedulesCount").textContent = String((data.schedules || []).length);
    $("schedulesTable").innerHTML = (data.schedules || []).length
      ? data.schedules.map((item) => `
          <tr>
            <td>
              <div class="row-title">${escapeHtml(item.title)}</div>
              <div class="row-sub">${escapeHtml(item.start_date || "-")} ~ ${escapeHtml(item.end_date || "-")}</div>
            </td>
            <td>${escapeHtml(item.schedule_type || "-")}</td>
            <td>${escapeHtml(item.assignee_name || "-")}</td>
            <td>${escapeHtml(item.task_title || "-")}</td>
            <td>
              <div class="actions">
                <button class="button sm ghost" type="button" data-edit-schedule="${item.id}">수정</button>
                <button class="button sm danger" type="button" data-delete-schedule="${item.id}">삭제</button>
              </div>
            </td>
          </tr>
        `).join("")
      : `<tr><td colspan="5"><div class="empty">등록된 일정이 없습니다.</div></td></tr>`;
  }

  function resetScheduleForm() {
    $("schedulesForm").reset();
    $("scheduleId").value = "";
    $("scheduleFormTitle").textContent = "새 일정";
  }

  $("scheduleResetButton").addEventListener("click", resetScheduleForm);
  $("schedulesTable").addEventListener("click", async (event) => {
    const edit = event.target.closest("[data-edit-schedule]");
    const del = event.target.closest("[data-delete-schedule]");
    if (edit) {
      const id = edit.getAttribute("data-edit-schedule");
      const detail = await fetchJson(`/api/schedules/${id}`);
      $("scheduleId").value = detail.id;
      $("scheduleTitle").value = detail.title || "";
      setSelectValue("scheduleType", detail.schedule_type || (constants.scheduleTypes || [])[0] || "");
      setSelectValue("scheduleAssigneeId", detail.assignee_id || "");
      setSelectValue("scheduleWbsTaskId", detail.wbs_task_id || "");
      $("scheduleStartDate").value = detail.start_date || "";
      $("scheduleEndDate").value = detail.end_date || "";
      $("scheduleDescription").value = detail.description || "";
      $("scheduleFormTitle").textContent = `일정 #${id} 수정`;
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (del) {
      const id = del.getAttribute("data-delete-schedule");
      if (!confirm(`일정 #${id}를 삭제할까요?`)) return;
      await fetchJson(`/api/schedules/${id}`, { method: "DELETE" });
      showToast("일정을 삭제했습니다.");
      resetScheduleForm();
      await loadSchedules();
    }
  });

  $("schedulesForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = $("scheduleId").value;
    const payload = {
      title: $("scheduleTitle").value.trim(),
      description: $("scheduleDescription").value,
      start_date: $("scheduleStartDate").value,
      end_date: $("scheduleEndDate").value,
      assignee_id: $("scheduleAssigneeId").value ? Number($("scheduleAssigneeId").value) : null,
      wbs_task_id: $("scheduleWbsTaskId").value ? Number($("scheduleWbsTaskId").value) : null,
      schedule_type: $("scheduleType").value,
    };
    await fetchJson(id ? `/api/schedules/${id}` : "/api/schedules", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(id ? "일정을 수정했습니다." : "일정을 생성했습니다.");
    resetScheduleForm();
    await loadSchedules();
  });

  resetScheduleForm();
  await loadSchedules();
}

async function initMembersPage() {
  async function loadMembers() {
    const data = await fetchJson("/api/members");
    $("membersCount").textContent = String((data.members || []).length);
    $("membersTable").innerHTML = (data.members || []).length
      ? data.members.map((item) => `
          <tr>
            <td>
              <div class="row-title">${escapeHtml(item.name)}</div>
              <div class="row-sub">${item.is_active ? "활성" : "비활성"}</div>
            </td>
            <td>${escapeHtml(item.role || "-")}</td>
            <td>${escapeHtml(item.part || "-")}</td>
            <td>${escapeHtml(item.contact || "-")}</td>
            <td>${escapeHtml(item.task_count ?? 0)}</td>
            <td>${escapeHtml(item.schedule_count ?? 0)}</td>
            <td>
              <div class="actions">
                <button class="button sm ghost" type="button" data-edit-member="${item.id}">수정</button>
                <button class="button sm danger" type="button" data-delete-member="${item.id}">삭제</button>
              </div>
            </td>
          </tr>
        `).join("")
      : `<tr><td colspan="7"><div class="empty">등록된 멤버가 없습니다.</div></td></tr>`;
  }

  function resetMemberForm() {
    $("membersForm").reset();
    $("memberId").value = "";
    $("memberActive").checked = true;
    $("memberFormTitle").textContent = "새 멤버";
  }

  $("memberResetButton").addEventListener("click", resetMemberForm);
  $("membersTable").addEventListener("click", async (event) => {
    const edit = event.target.closest("[data-edit-member]");
    const del = event.target.closest("[data-delete-member]");
    if (edit) {
      const id = edit.getAttribute("data-edit-member");
      const detail = await fetchJson(`/api/members/${id}`);
      const member = detail.member;
      $("memberId").value = member.id;
      $("memberName").value = member.name || "";
      $("memberRole").value = member.role || "";
      $("memberPart").value = member.part || "";
      $("memberContact").value = member.contact || "";
      $("memberActive").checked = Boolean(member.is_active);
      $("memberFormTitle").textContent = `멤버 #${id} 수정`;
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (del) {
      const id = del.getAttribute("data-delete-member");
      if (!confirm(`멤버 #${id}를 삭제할까요?`)) return;
      await fetchJson(`/api/members/${id}`, { method: "DELETE" });
      showToast("멤버를 삭제했습니다.");
      resetMemberForm();
      await loadMembers();
    }
  });

  $("membersForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = $("memberId").value;
    const payload = {
      name: $("memberName").value.trim(),
      role: $("memberRole").value.trim(),
      part: $("memberPart").value.trim(),
      contact: $("memberContact").value.trim(),
      is_active: $("memberActive").checked ? 1 : 0,
    };
    await fetchJson(id ? `/api/members/${id}` : "/api/members", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(id ? "멤버를 수정했습니다." : "멤버를 생성했습니다.");
    resetMemberForm();
    await loadMembers();
  });

  resetMemberForm();
  await loadMembers();
}

async function boot() {
  try {
    const page = $body.dataset.page;
    if (page === "dashboard") await initDashboardPage();
    if (page === "documents-list") await initDocumentsListPage();
    if (page === "document-form") await initDocumentFormPage();
    if (page === "document-detail") await initDocumentDetailPage();
    if (page === "wbs") await initWbsPage();
    if (page === "schedules") await initSchedulesPage();
    if (page === "members") await initMembersPage();
  } catch (error) {
    showToast(error.message || "페이지 초기화에 실패했습니다.", true);
    console.error(error);
  }
}

boot();
"""


def _nav_link(label: str, href: str, active: str, current: str) -> str:
    cls = "nav-link is-active" if active == current else "nav-link"
    return f'<a class="{cls}" href="{href}">{label}</a>'


def render_layout(
    *,
    title: str,
    eyebrow: str,
    page_title: str,
    subtitle: str,
    active_nav: str,
    body: str,
    actions: str = "",
    page_key: str,
    extra_data: str = "",
) -> str:
    nav = "".join(
        [
            _nav_link("대시보드", "/dashboard", active_nav, "dashboard"),
            _nav_link("WBS", "/wbs", active_nav, "wbs"),
            _nav_link("문서", "/documents", active_nav, "documents"),
            _nav_link("일정", "/schedules", active_nav, "schedules"),
            _nav_link("멤버", "/members", active_nav, "members"),
        ]
    )
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="/static/worker.css" />
    <script>
      window.WORKER_CONSTANTS = {extra_data or "{}"};
    </script>
    <script defer src="/static/worker.js"></script>
  </head>
  <body data-page="{page_key}">
    <div class="app-shell">
      <aside class="sidebar">
        <p class="sidebar__eyebrow">INTERNAL</p>
        <a class="sidebar__title" href="/dashboard">AGENTIC PRODUCT STUDIO DEV<br />Docs</a>
        <p class="sidebar__caption">문서, WBS, 일정, 팀 협업을 한 곳에서 관리합니다.</p>
        <nav class="sidebar__nav">{nav}</nav>
        <div class="sidebar__note">
          <p class="section-eyebrow">Core Focus</p>
          <strong>라우팅된 운영 화면</strong>
          <p>Cloudflare Worker 기준으로도 실제 사용 가능한 작업 흐름이 되도록 화면 책임을 분리했습니다.</p>
        </div>
      </aside>
      <main class="main-shell">
        <header class="topbar">
          <div>
            <p class="topbar__eyebrow">{eyebrow}</p>
            <h1 class="topbar__title">{page_title}</h1>
            <p class="topbar__subtitle">{subtitle}</p>
          </div>
          <div class="topbar__actions">{actions}</div>
        </header>
        <div class="page-content">{body}</div>
      </main>
    </div>
    <div class="toast" id="toast"></div>
  </body>
</html>"""


def render_dashboard_page(constants_json: str) -> str:
    body = """
    <section class="panel">
      <div class="panel-body stack">
        <div id="runtimePills" class="actions"></div>
        <div id="dashboardStats" class="stats-grid"></div>
      </div>
    </section>
    <section class="split-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2>예정 일정</h2>
            <p>이번 주 기준으로 확인해야 할 일정을 모아봅니다.</p>
          </div>
        </div>
        <div class="panel-body"><div id="dashboardUpcoming" class="stack"></div></div>
      </article>
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2>최근 문서</h2>
            <p>가장 최근에 수정된 문서를 바로 확인합니다.</p>
          </div>
        </div>
        <div class="panel-body"><div id="dashboardRecentDocs" class="stack"></div></div>
      </article>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>최근 작업</h2>
          <p>최근 갱신된 WBS 작업을 빠르게 점검합니다.</p>
        </div>
      </div>
      <div class="panel-body"><div id="dashboardRecentTasks" class="stack"></div></div>
    </section>
    """
    return render_layout(
        title="대시보드 | Agentic Product Studio",
        eyebrow="WORKSPACE",
        page_title="대시보드",
        subtitle="Cloudflare Worker와 D1/R2 기준 운영 상태와 최근 활동을 한 번에 확인합니다.",
        active_nav="dashboard",
        page_key="dashboard",
        actions='<a class="button primary" href="/documents/new">새 문서</a>',
        body=body,
        extra_data=constants_json,
    )


def render_documents_list_page(constants_json: str) -> str:
    body = """
    <section class="panel">
      <div class="panel-body">
        <form id="docsFilterForm" class="field-grid">
          <div class="field">
            <label for="docsFilterQuery">검색</label>
            <input id="docsFilterQuery" type="text" placeholder="제목 또는 내용 검색" />
          </div>
          <div class="field">
            <label for="docsFilterType">문서 유형</label>
            <select id="docsFilterType"></select>
          </div>
          <div class="field">
            <label for="docsFilterFolder">폴더</label>
            <select id="docsFilterFolder"></select>
          </div>
          <div class="field" style="align-self:end;">
            <button class="button primary" type="submit">필터 적용</button>
          </div>
        </form>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>문서 목록</h2>
          <p>전체 문서 수: <strong id="docsCount">0</strong></p>
        </div>
      </div>
      <div class="panel-body table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>제목</th>
              <th>유형</th>
              <th>작성자</th>
              <th>수정일</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody id="docsTable"></tbody>
        </table>
      </div>
    </section>
    """
    return render_layout(
        title="문서 | Agentic Product Studio",
        eyebrow="DOCUMENTS",
        page_title="문서",
        subtitle="목록, 상세, 작성 화면을 분리해 실제 문서 작성 흐름에 맞게 운영합니다.",
        active_nav="documents",
        page_key="documents-list",
        actions='<a class="button primary" href="/documents/new">새 문서</a>',
        body=body,
        extra_data=constants_json,
    )


def render_document_form_page(constants_json: str, document_id: int | None) -> str:
    title = "문서 수정" if document_id else "새 문서"
    body = f"""
    <section id="documentFormPage" data-document-id="{document_id or ''}" class="docs-editor-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2>{title}</h2>
            <p>에디터 폭을 충분히 확보하고, Markdown preview와 R2 이미지 업로드를 바로 연결합니다.</p>
          </div>
        </div>
        <div class="panel-body stack">
          <form id="documentForm" class="stack">
            <input type="hidden" id="documentAssetDraftKey" />
            <div class="field">
              <label for="documentTitle">제목</label>
              <input id="documentTitle" required />
            </div>
            <div class="field-grid">
              <div class="field"><label for="documentDocType">문서 유형</label><select id="documentDocType"></select></div>
              <div class="field"><label for="documentFolderId">폴더</label><select id="documentFolderId"></select></div>
              <div class="field"><label for="documentNewFolderName">새 폴더명</label><input id="documentNewFolderName" placeholder="필요 시 새 폴더 생성" /></div>
              <div class="field"><label for="documentAuthorId">작성자</label><select id="documentAuthorId"></select></div>
            </div>
            <div class="field">
              <label for="documentTags">태그</label>
              <input id="documentTags" placeholder="쉼표로 구분" />
            </div>
            <div class="field">
              <label for="documentRelatedTaskIds">연결 작업</label>
              <select id="documentRelatedTaskIds" multiple size="6"></select>
            </div>
            <div class="toolbar" id="documentToolbar">
              <button class="button sm ghost" type="button" data-insert="# {{selection}}">H1</button>
              <button class="button sm ghost" type="button" data-insert="## {{selection}}">H2</button>
              <button class="button sm ghost" type="button" data-insert="- {{selection}}">List</button>
              <button class="button sm ghost" type="button" data-insert="**{{selection}}**">Bold</button>
              <button class="button sm ghost" type="button" data-insert="`{{selection}}`">Code</button>
              <button class="button sm ghost" type="button" data-insert="```\n{{selection}}\n```">Block</button>
              <button class="button sm ghost" type="button" data-format-markdown>코드 정리</button>
              <button class="button sm primary" type="button" data-upload-image>이미지 업로드</button>
              <span class="spacer"></span>
              <span class="helper" id="documentEditorStatus">미리보기 준비 중...</span>
            </div>
            <input id="documentImageInput" type="file" accept="image/*" hidden />
            <div class="markdown-panes">
              <div class="markdown-pane">
                <span class="markdown-pane-label">Editor</span>
                <textarea id="documentContent" class="markdown-editor" placeholder="Markdown 본문 입력"></textarea>
              </div>
              <div class="markdown-pane">
                <span class="markdown-pane-label">Preview</span>
                <div id="documentPreview" class="markdown-preview"></div>
              </div>
            </div>
            <label class="helper"><input id="documentHidden" type="checkbox" /> 숨김 문서로 저장</label>
            <div class="actions">
              <button class="button primary" type="submit">저장</button>
              <a class="button ghost" href="/documents">목록으로</a>
            </div>
          </form>
        </div>
      </article>
      <aside class="panel">
        <div class="panel-head">
          <div>
            <h3>작성 가이드</h3>
            <p>실무에서 바로 쓰기 좋도록 문서 작성 화면 자체를 넓게 구성했습니다.</p>
          </div>
        </div>
        <div class="panel-body stack">
          <div class="feed-item">
            <strong>이미지 업로드</strong>
            <div class="meta">버튼 업로드, 클립보드 붙여넣기, 드래그 앤 드롭 모두 지원합니다.</div>
          </div>
          <div class="feed-item">
            <strong>Markdown 정리</strong>
            <div class="meta">Python, JSON, SQL, YAML, HTML 계열 코드블록 자동 정리를 지원합니다.</div>
          </div>
          <div class="feed-item">
            <strong>자산 연결</strong>
            <div class="meta">문서 저장 전 업로드한 이미지는 draft key로 묶였다가 저장 시 문서 자산으로 귀속됩니다.</div>
          </div>
        </div>
      </aside>
    </section>
    """
    return render_layout(
        title=f"{title} | Agentic Product Studio",
        eyebrow="DOCUMENTS",
        page_title=title,
        subtitle="문서 작성 자체가 작업이 되도록, 좁은 임시 폼이 아니라 편집 중심 화면으로 재구성했습니다.",
        active_nav="documents",
        page_key="document-form",
        actions='<a class="button ghost" href="/documents">문서 목록</a>' if not document_id else f'<a class="button ghost" href="/documents/{document_id}">문서 보기</a>',
        body=body,
        extra_data=constants_json,
    )


def render_document_detail_page(constants_json: str, document_id: int) -> str:
    body = f"""
    <section id="documentDetailPage" data-document-id="{document_id}" class="docs-editor-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2 id="documentDetailTitle">문서 로딩 중...</h2>
            <p id="documentDetailMeta">문서 정보를 불러오는 중입니다.</p>
          </div>
        </div>
        <div class="panel-body detail-shell">
          <div id="documentDetailTags" class="actions"></div>
          <div id="documentDetailBody" class="detail-content"></div>
        </div>
      </article>
      <aside class="panel">
        <div class="panel-head">
          <div>
            <h3>문서 메타데이터</h3>
            <p>연결 작업과 이미지 자산을 함께 확인합니다.</p>
          </div>
        </div>
        <div class="panel-body stack">
          <section>
            <p class="section-eyebrow">Linked Tasks</p>
            <div id="documentDetailTasks" class="stack"></div>
          </section>
          <section>
            <p class="section-eyebrow">Image Assets</p>
            <div id="documentDetailAssets" class="stack"></div>
          </section>
        </div>
      </aside>
    </section>
    """
    return render_layout(
        title="문서 상세 | Agentic Product Studio",
        eyebrow="DOCUMENTS",
        page_title="문서 상세",
        subtitle="본문 렌더링과 자산 관리를 분리해 문서 조회와 정리가 모두 가능하도록 구성했습니다.",
        active_nav="documents",
        page_key="document-detail",
        actions=f'<a class="button primary" href="/documents/{document_id}/edit">문서 수정</a><a class="button ghost" href="/documents">문서 목록</a>',
        body=body,
        extra_data=constants_json,
    )


def render_wbs_page(constants_json: str) -> str:
    body = """
    <section class="split-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2>WBS 필터</h2>
            <p>상태, 담당자, 우선순위, 플랫폼 기준으로 작업을 좁혀봅니다.</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="wbsFilterForm" class="field-grid">
            <div class="field"><label for="wbsFilterStatus">상태</label><select id="wbsFilterStatus"></select></div>
            <div class="field"><label for="wbsFilterAssigneeId">담당자</label><select id="wbsFilterAssigneeId"></select></div>
            <div class="field"><label for="wbsFilterPriority">우선순위</label><select id="wbsFilterPriority"></select></div>
            <div class="field"><label for="wbsFilterPlatform">플랫폼</label><select id="wbsFilterPlatform"></select></div>
            <div class="field full actions"><button class="button primary" type="submit">필터 적용</button></div>
          </form>
        </div>
      </article>
      <aside class="panel">
        <div class="panel-head">
          <div>
            <h2 id="wbsFormTitle">새 작업</h2>
            <p>라우팅은 분리하되, WBS는 한 화면에서 빠르게 수정 가능한 운영형 구조로 유지합니다.</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="wbsForm" class="stack">
            <input type="hidden" id="wbsId" />
            <div class="field"><label for="wbsTitle">작업명</label><input id="wbsTitle" required /></div>
            <div class="field-grid">
              <div class="field"><label for="wbsParentId">상위 작업</label><select id="wbsParentId"></select></div>
              <div class="field"><label for="wbsAssigneeId">담당자</label><select id="wbsAssigneeId"></select></div>
              <div class="field"><label for="wbsPlatform">플랫폼</label><select id="wbsPlatform"></select></div>
              <div class="field"><label for="wbsStatus">상태</label><select id="wbsStatus"></select></div>
              <div class="field"><label for="wbsPriority">우선순위</label><select id="wbsPriority"></select></div>
              <div class="field"><label for="wbsProgress">진행률</label><input id="wbsProgress" type="number" min="0" max="100" value="0" /></div>
              <div class="field"><label for="wbsStartDate">시작일</label><input id="wbsStartDate" type="date" /></div>
              <div class="field"><label for="wbsDueDate">마감일</label><input id="wbsDueDate" type="date" /></div>
              <div class="field"><label for="wbsCompletedDate">완료일</label><input id="wbsCompletedDate" type="date" /></div>
            </div>
            <div class="field"><label for="wbsDocumentIds">연결 문서</label><select id="wbsDocumentIds" multiple size="6"></select></div>
            <div class="field"><label for="wbsDescription">설명</label><textarea id="wbsDescription"></textarea></div>
            <div class="field"><label for="wbsNotes">메모</label><textarea id="wbsNotes"></textarea></div>
            <div class="actions">
              <button class="button primary" type="submit">저장</button>
              <button class="button ghost" type="button" id="wbsResetButton">초기화</button>
            </div>
          </form>
        </div>
      </aside>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>작업 목록</h2>
          <p>전체 작업 수: <strong id="wbsCount">0</strong></p>
        </div>
      </div>
      <div class="panel-body table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>작업</th>
              <th>상태</th>
              <th>우선순위</th>
              <th>진행률</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody id="wbsTable"></tbody>
        </table>
      </div>
    </section>
    """
    return render_layout(
        title="WBS | Agentic Product Studio",
        eyebrow="WORK BREAKDOWN STRUCTURE",
        page_title="WBS 작업 관리",
        subtitle="필터 영역과 편집 영역을 분리해 한 화면에서도 관리가 쉬운 WBS 구조로 정리했습니다.",
        active_nav="wbs",
        page_key="wbs",
        body=body,
        extra_data=constants_json,
    )


def render_schedules_page(constants_json: str) -> str:
    body = """
    <section class="split-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2>일정 입력</h2>
            <p>작업과 연결된 일정을 한 곳에서 입력하고 관리합니다.</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="schedulesForm" class="stack">
            <input type="hidden" id="scheduleId" />
            <div class="field"><label for="scheduleTitle">일정명</label><input id="scheduleTitle" required /></div>
            <div class="field-grid">
              <div class="field"><label for="scheduleType">일정 유형</label><select id="scheduleType"></select></div>
              <div class="field"><label for="scheduleAssigneeId">담당자</label><select id="scheduleAssigneeId"></select></div>
              <div class="field"><label for="scheduleWbsTaskId">연결 WBS</label><select id="scheduleWbsTaskId"></select></div>
              <div class="field"><label for="scheduleStartDate">시작일</label><input id="scheduleStartDate" type="date" /></div>
              <div class="field"><label for="scheduleEndDate">종료일</label><input id="scheduleEndDate" type="date" /></div>
            </div>
            <div class="field"><label for="scheduleDescription">설명</label><textarea id="scheduleDescription"></textarea></div>
            <div class="actions">
              <button class="button primary" type="submit">저장</button>
              <button class="button ghost" type="button" id="scheduleResetButton">초기화</button>
            </div>
          </form>
        </div>
      </article>
      <aside class="panel">
        <div class="panel-head">
          <div>
            <h2 id="scheduleFormTitle">새 일정</h2>
            <p>목록에서 선택하면 같은 화면에서 바로 수정할 수 있습니다.</p>
          </div>
        </div>
        <div class="panel-body"><div class="empty">좌측 폼으로 일정을 생성하거나, 아래 목록에서 편집할 일정을 선택하세요.</div></div>
      </aside>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>일정 목록</h2>
          <p>전체 일정 수: <strong id="schedulesCount">0</strong></p>
        </div>
      </div>
      <div class="panel-body table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>일정</th>
              <th>유형</th>
              <th>담당자</th>
              <th>연결 작업</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody id="schedulesTable"></tbody>
        </table>
      </div>
    </section>
    """
    return render_layout(
        title="일정 | Agentic Product Studio",
        eyebrow="SCHEDULES",
        page_title="일정",
        subtitle="주요 일정 작성과 수정 흐름을 별도 페이지로 분리해 운영 화면을 안정적으로 유지합니다.",
        active_nav="schedules",
        page_key="schedules",
        body=body,
        extra_data=constants_json,
    )


def render_members_page(constants_json: str) -> str:
    body = """
    <section class="split-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2 id="memberFormTitle">새 멤버</h2>
            <p>멤버 생성과 수정은 별도 탭 이동 없이 같은 화면에서 처리합니다.</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="membersForm" class="stack">
            <input type="hidden" id="memberId" />
            <div class="field"><label for="memberName">이름</label><input id="memberName" required /></div>
            <div class="field-grid">
              <div class="field"><label for="memberRole">역할</label><input id="memberRole" /></div>
              <div class="field"><label for="memberPart">파트</label><input id="memberPart" /></div>
              <div class="field full"><label for="memberContact">연락처</label><input id="memberContact" /></div>
            </div>
            <label class="helper"><input id="memberActive" type="checkbox" checked /> 활성 멤버로 등록</label>
            <div class="actions">
              <button class="button primary" type="submit">저장</button>
              <button class="button ghost" type="button" id="memberResetButton">초기화</button>
            </div>
          </form>
        </div>
      </article>
      <aside class="panel">
        <div class="panel-head">
          <div>
            <h2>멤버 운영</h2>
            <p>WBS, 일정, 문서 작성자 선택에서 참조하는 인원 정보를 관리합니다.</p>
          </div>
        </div>
        <div class="panel-body"><div class="empty">멤버를 선택하면 이 폼에서 바로 수정할 수 있습니다.</div></div>
      </aside>
    </section>
    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>멤버 목록</h2>
          <p>전체 멤버 수: <strong id="membersCount">0</strong></p>
        </div>
      </div>
      <div class="panel-body table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>멤버</th>
              <th>역할</th>
              <th>파트</th>
              <th>연락처</th>
              <th>작업 수</th>
              <th>일정 수</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody id="membersTable"></tbody>
        </table>
      </div>
    </section>
    """
    return render_layout(
        title="멤버 | Agentic Product Studio",
        eyebrow="MEMBERS",
        page_title="멤버 관리",
        subtitle="작업과 일정, 문서 작성자를 모두 참조하는 팀 멤버 정보를 운영형 화면으로 분리했습니다.",
        active_nav="members",
        page_key="members",
        body=body,
        extra_data=constants_json,
    )
