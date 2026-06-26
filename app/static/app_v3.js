function initDocumentFolderForm() {
  const typeSelect = document.querySelector("[data-folder-type]");
  const folderSelect = document.querySelector("[data-folder-select]");
  if (!typeSelect || !folderSelect) return;

  const syncFolders = () => {
    const currentType = typeSelect.value;
    const options = Array.from(folderSelect.options);
    let selectedVisible = false;

    options.forEach((option, index) => {
      if (index === 0) {
        option.hidden = false;
        return;
      }

      const matches = option.dataset.docType === currentType;
      option.hidden = !matches;
      if (matches && option.selected) selectedVisible = true;
    });

    if (!selectedVisible) {
      folderSelect.value = "";
    }
  };

  typeSelect.addEventListener("change", syncFolders);
  syncFolders();
}

function buildScheduleItemMarkup(item) {
  const wbs = item.task_title
    ? `<span class="meta-chip"><span class="meta-key">WBS</span><span>${item.task_title}</span></span>`
    : "";
  const description = item.summary
    ? `<p class="modal-schedule__summary">${item.summary}</p>`
    : '<p class="modal-schedule__summary muted-text">설명 없음</p>';
  const range = `${item.start_date} ~ ${item.end_date}`;

  return `
    <article class="modal-schedule">
      <div class="modal-schedule__top">
        <strong>${item.title}</strong>
        <span class="badge badge--planned">${item.schedule_type}</span>
      </div>
      <div class="schedule-meta">
        <span class="meta-chip"><span class="meta-key">담당</span><span>${item.assignee_name}</span></span>
        ${wbs}
        <span class="meta-chip"><span class="meta-key">일정</span><span>${range}</span></span>
      </div>
      ${description}
    </article>
  `;
}

function initScheduleCalendarModal() {
  const modal = document.querySelector("[data-schedule-modal]");
  if (!modal) return;

  const title = modal.querySelector("[data-modal-title]");
  const body = modal.querySelector("[data-modal-body]");

  const closeModal = () => {
    modal.setAttribute("hidden", "hidden");
    document.body.classList.remove("modal-open");
  };

  const openModal = (dayLabel, items) => {
    title.textContent = dayLabel || "일정 상세";
    body.innerHTML = items.length
      ? items.map(buildScheduleItemMarkup).join("")
      : '<p class="empty-state">해당 날짜의 일정이 없습니다.</p>';
    modal.removeAttribute("hidden");
    document.body.classList.add("modal-open");
  };

  document.addEventListener("click", (event) => {
    const dayButton = event.target.closest("[data-calendar-day]");
    if (dayButton) {
      const items = JSON.parse(dayButton.dataset.dayItems || "[]");
      openModal(dayButton.dataset.dayLabel, items);
      return;
    }

    const closeTrigger = event.target.closest("[data-modal-close]");
    if (closeTrigger) {
      closeModal();
      return;
    }

    if (event.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hasAttribute("hidden")) {
      closeModal();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initDocumentFolderForm();
  initScheduleCalendarModal();
});
