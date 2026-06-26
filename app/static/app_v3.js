function initDocumentFolderForm() {
  const pairs = Array.from(document.querySelectorAll("[data-folder-type]")).map((typeSelect) => ({
    typeSelect,
    folderSelect: typeSelect
      .closest("form, .modal-card, .panel, body")
      ?.querySelector("[data-folder-select]"),
  }));

  pairs.forEach(({ typeSelect, folderSelect }) => {
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
  });
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
      <div class="schedule-meta schedule-meta--modal">
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
  const root = document.documentElement;

  const lockBodyScroll = () => {
    const scrollbarWidth = Math.max(window.innerWidth - root.clientWidth, 0);
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }
    document.body.classList.add("modal-open");
  };

  const unlockBodyScroll = () => {
    document.body.classList.remove("modal-open");
    document.body.style.paddingRight = "";
  };

  const closeModal = () => {
    modal.setAttribute("hidden", "hidden");
    unlockBodyScroll();
  };

  const openModal = (dayLabel, items) => {
    title.textContent = dayLabel || "일정 상세";
    body.innerHTML = items.length
      ? items.map(buildScheduleItemMarkup).join("")
      : '<p class="empty-state">해당 날짜의 일정이 없습니다.</p>';
    modal.removeAttribute("hidden");
    lockBodyScroll();
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

function initGenericModals() {
  const root = document.documentElement;
  const getModal = (id) => document.querySelector(`[data-modal-id="${id}"]`);

  const lockBodyScroll = () => {
    const scrollbarWidth = Math.max(window.innerWidth - root.clientWidth, 0);
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }
    document.body.classList.add("modal-open");
  };

  const unlockBodyScroll = () => {
    document.body.classList.remove("modal-open");
    document.body.style.paddingRight = "";
  };

  const closeModal = (modal) => {
    if (!modal) return;
    modal.setAttribute("hidden", "hidden");
    unlockBodyScroll();
  };

  const openModal = (modal) => {
    if (!modal) return;
    modal.removeAttribute("hidden");
    lockBodyScroll();
  };

  document.addEventListener("click", (event) => {
    const openTrigger = event.target.closest("[data-modal-open]");
    if (openTrigger) {
      openModal(getModal(openTrigger.dataset.modalOpen));
      return;
    }

    const closeTrigger = event.target.closest("[data-modal-close]");
    if (closeTrigger) {
      closeModal(closeTrigger.closest(".modal-backdrop"));
      return;
    }

    const backdrop = event.target.closest(".modal-backdrop[data-modal-id]");
    if (backdrop && event.target === backdrop) {
      closeModal(backdrop);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const openedModal = document.querySelector(".modal-backdrop[data-modal-id]:not([hidden])");
    if (openedModal) {
      closeModal(openedModal);
    }
  });
}

function initDocumentFolderManageModal() {
  const form = document.querySelector("[data-document-folder-form]");
  if (!form) return;

  const currentText = document.querySelector("[data-document-folder-current]");
  const typeSelect = form.querySelector("[data-folder-type]");
  const folderSelect = form.querySelector("[data-folder-select]");

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-document-folder-open]");
    if (!trigger) return;

    form.action = trigger.dataset.folderAction;
    if (currentText) {
      currentText.textContent = trigger.dataset.documentTitle || "대상 문서를 선택하세요.";
    }
    if (typeSelect) {
      typeSelect.value = trigger.dataset.documentType || "";
      typeSelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (folderSelect) {
      folderSelect.value = trigger.dataset.folderId || "";
    }
  });
}

function initWbsFormAutoComplete() {
  const form = document.querySelector("[data-wbs-form]");
  if (!form) return;

  const statusField = form.querySelector("[data-wbs-status]");
  const progressField = form.querySelector("[data-wbs-progress]");
  const completedDateField = form.querySelector("[data-wbs-completed-date]");
  const completedStatus = form.dataset.completedStatus || "완료";

  if (!statusField || !progressField || !completedDateField) return;

  const today = new Date();
  const todayLocal = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");

  const syncCompletedState = () => {
    if (statusField.value === completedStatus) {
      progressField.value = "100";
      if (!completedDateField.value) {
        completedDateField.value = todayLocal;
      }
    }
  };

  statusField.addEventListener("change", syncCompletedState);
  syncCompletedState();
}

document.addEventListener("DOMContentLoaded", () => {
  initDocumentFolderForm();
  initDocumentFolderManageModal();
  initGenericModals();
  initScheduleCalendarModal();
  initWbsFormAutoComplete();
});
