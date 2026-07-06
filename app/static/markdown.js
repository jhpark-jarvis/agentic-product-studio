function debounce(fn, delay) {
  let timeoutId = null;
  return (...args) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

function setupMarkdownEditor() {
  const editorRoot = document.querySelector("[data-markdown-editor]");
  if (!editorRoot) {
    return;
  }

  const textarea = editorRoot.querySelector("textarea");
  const preview = editorRoot.querySelector("[data-markdown-preview]");
  const buttons = editorRoot.querySelectorAll("[data-md-insert]");
  const formatButton = editorRoot.querySelector("[data-md-format]");
  const uploadButton = editorRoot.querySelector("[data-md-upload-image]");
  const linkSearchButton = editorRoot.querySelector("[data-md-open-link-search]");
  const imageInput = editorRoot.querySelector("[data-md-image-input]");
  const linkModal = editorRoot.querySelector("[data-md-link-modal]");
  const linkQueryInput = editorRoot.querySelector("[data-md-link-query]");
  const linkResults = editorRoot.querySelector("[data-md-link-results]");
  const linkCloseButton = editorRoot.querySelector("[data-md-link-close]");
  const status = editorRoot.querySelector("[data-markdown-status]");
  const documentId = editorRoot.dataset.documentId || "";
  const draftKey = editorRoot.dataset.draftKey || "";
  const previewUrl = editorRoot.dataset.previewUrl;
  const formatUrl = editorRoot.dataset.formatUrl;
  const uploadUrl = editorRoot.dataset.uploadUrl;
  const linkSearchUrl = editorRoot.dataset.linkSearchUrl;
  let isUploading = false;

  const setStatus = (message) => {
    if (status) {
      status.textContent = message;
    }
  };

  const setUploadingState = (uploading) => {
    isUploading = uploading;
    editorRoot.classList.toggle("markdown-editor--uploading", uploading);
    if (uploadButton) {
      uploadButton.disabled = uploading;
    }
    if (formatButton) {
      formatButton.disabled = uploading;
    }
  };

  const clearDragState = () => {
    editorRoot.classList.remove("markdown-editor--dragover");
  };

  const insertSnippet = (snippet) => {
    const start = textarea.selectionStart ?? textarea.value.length;
    const end = textarea.selectionEnd ?? textarea.value.length;
    const selected = textarea.value.slice(start, end);
    const text = snippet.includes("{selection}")
      ? snippet.replace("{selection}", selected || "text")
      : snippet;

    textarea.setRangeText(text, start, end, "end");
    textarea.focus();
    textarea.dispatchEvent(new Event("input"));
  };

  const escapeHtml = (value) =>
    (value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

  const buildAbsoluteUrl = (path) => {
    try {
      return new URL(path, window.location.origin).toString();
    } catch (_error) {
      return path;
    }
  };

  const insertDocumentLink = (title, path) => {
    insertSnippet(`[${title}](${path})`);
    if (linkModal?.open) {
      linkModal.close();
    }
    setStatus("문서 링크를 본문에 삽입했습니다");
  };

  const copyDocumentLink = async (path) => {
    await navigator.clipboard.writeText(buildAbsoluteUrl(path));
    setStatus("문서 URL을 클립보드에 복사했습니다");
  };

  const renderLinkResults = (items) => {
    if (!linkResults) {
      return;
    }

    if (!items.length) {
      linkResults.innerHTML = "<p class='muted-text'>검색 결과가 없습니다.</p>";
      return;
    }

    linkResults.innerHTML = items
      .map((item) => {
        const hiddenBadge = item.is_hidden
          ? "<span class='document-link-result__badge'>숨김</span>"
          : "";
        const folderLabel = item.folder_name
          ? escapeHtml(item.folder_name)
          : "폴더 없음";

        return `
          <article class="document-link-result">
            <div class="document-link-result__body">
              <div class="document-link-result__title-row">
                <strong>${escapeHtml(item.title)}</strong>
                ${hiddenBadge}
              </div>
              <div class="document-link-result__meta">
                <span>${escapeHtml(item.doc_type || "")}</span>
                <span>${folderLabel}</span>
              </div>
              <code class="document-link-result__path">${escapeHtml(item.path)}</code>
            </div>
            <div class="document-link-result__actions">
              <button type="button" class="toolbar-button" data-link-copy="${escapeHtml(item.path)}">URL 복사</button>
              <button
                type="button"
                class="toolbar-button toolbar-button--accent"
                data-link-insert="${escapeHtml(item.path)}"
                data-link-title="${escapeHtml(item.title)}"
              >
                URL 삽입
              </button>
            </div>
          </article>
        `;
      })
      .join("");
  };

  const searchDocumentLinks = debounce(async () => {
    if (!linkSearchUrl || !linkQueryInput || !linkResults) {
      return;
    }

    const keyword = linkQueryInput.value.trim();
    if (!keyword) {
      linkResults.innerHTML = "<p class='muted-text'>문서 제목을 입력하면 결과가 표시됩니다.</p>";
      return;
    }

    linkResults.innerHTML = "<p class='muted-text'>문서를 검색하는 중입니다...</p>";

    try {
      const url = new URL(linkSearchUrl, window.location.origin);
      url.searchParams.set("q", keyword);
      url.searchParams.set("limit", "12");

      const response = await fetch(url.toString(), { method: "GET" });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "문서 검색에 실패했습니다");
      }
      renderLinkResults(payload.items || []);
    } catch (error) {
      linkResults.innerHTML = `<p class='muted-text'>${escapeHtml(error?.message || "문서 검색에 실패했습니다")}</p>`;
    }
  }, 180);

  buttons.forEach((button) => {
    button.addEventListener("click", () => insertSnippet(button.dataset.mdInsert || ""));
  });

  const uploadSelectedImage = async (file) => {
    if (!file || !uploadUrl || isUploading) {
      return;
    }
    if (!file.type.startsWith("image/")) {
      setStatus("Only image files can be uploaded");
      return;
    }

    setUploadingState(true);
    setStatus("Uploading image...");
    const body = new FormData();
    body.set("image", file);
    body.set("alt", file.name.replace(/\.[^.]+$/, ""));
    if (documentId) {
      body.set("document_id", documentId);
    }
    if (draftKey) {
      body.set("draft_key", draftKey);
    }

    try {
      const response = await fetch(uploadUrl, {
        method: "POST",
        body,
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Upload failed");
      }

      insertSnippet(`\n${payload.markdown}\n`);
      setStatus("Image uploaded");
    } catch (error) {
      setStatus(error?.message || "Image upload failed");
    } finally {
      setUploadingState(false);
      if (imageInput) {
        imageInput.value = "";
      }
    }
  };

  if (uploadButton && imageInput && uploadUrl) {
    uploadButton.addEventListener("click", () => imageInput.click());

    imageInput.addEventListener("change", async () => {
      const [file] = imageInput.files || [];
      await uploadSelectedImage(file);
    });
  }

  if (linkSearchButton && linkModal) {
    linkSearchButton.addEventListener("click", () => {
      linkModal.showModal();
      if (linkQueryInput) {
        linkQueryInput.focus();
        linkQueryInput.select();
      }
    });
  }

  if (linkCloseButton && linkModal) {
    linkCloseButton.addEventListener("click", () => linkModal.close());
  }

  if (linkQueryInput) {
    linkQueryInput.addEventListener("input", searchDocumentLinks);
    linkQueryInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchDocumentLinks();
      }
    });
  }

  if (linkModal) {
    linkModal.addEventListener("click", (event) => {
      if (event.target === linkModal) {
        linkModal.close();
      }
    });

    linkModal.addEventListener("close", () => {
      if (linkQueryInput) {
        linkQueryInput.value = "";
      }
      if (linkResults) {
        linkResults.innerHTML = "<p class='muted-text'>문서 제목을 입력하면 결과가 표시됩니다.</p>";
      }
    });
  }

  if (linkResults) {
    linkResults.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      const copyPath = target.dataset.linkCopy;
      if (copyPath) {
        try {
          await copyDocumentLink(copyPath);
        } catch (_error) {
          setStatus("클립보드 복사에 실패했습니다");
        }
        return;
      }

      const insertPath = target.dataset.linkInsert;
      if (insertPath) {
        insertDocumentLink(target.dataset.linkTitle || "문서", insertPath);
      }
    });
  }

  ["dragenter", "dragover"].forEach((eventName) => {
    editorRoot.addEventListener(eventName, (event) => {
      event.preventDefault();
      editorRoot.classList.add("markdown-editor--dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    editorRoot.addEventListener(eventName, (event) => {
      event.preventDefault();
      if (eventName === "dragleave" && editorRoot.contains(event.relatedTarget)) {
        return;
      }
      clearDragState();
    });
  });

  editorRoot.addEventListener("drop", async (event) => {
    const [file] = Array.from(event.dataTransfer?.files || []);
    await uploadSelectedImage(file);
  });

  textarea.addEventListener("paste", async (event) => {
    const items = Array.from(event.clipboardData?.items || []);
    const imageItem = items.find((item) => item.type?.startsWith("image/"));
    if (!imageItem) {
      return;
    }

    const file = imageItem.getAsFile();
    if (!file) {
      setStatus("Clipboard image could not be read");
      return;
    }

    event.preventDefault();
    await uploadSelectedImage(file);
  });

  if (formatButton && formatUrl) {
    formatButton.addEventListener("click", async () => {
      setStatus("Formatting code blocks...");
      const body = new URLSearchParams();
      body.set("content", textarea.value);

      try {
        const response = await fetch(formatUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          },
          body: body.toString(),
        });
        const payload = await response.json();
        textarea.value = payload.content || textarea.value;
        textarea.dispatchEvent(new Event("input"));
        setStatus("Formatting applied");
      } catch (_error) {
        setStatus("Formatting failed");
      }
    });
  }

  const renderPreview = debounce(async () => {
    if (!previewUrl) {
      return;
    }

    if (!isUploading) {
      setStatus("Rendering preview...");
    }
    const body = new URLSearchParams();
    body.set("content", textarea.value);

    try {
      const response = await fetch(previewUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        body: body.toString(),
      });
      const payload = await response.json();
      preview.innerHTML = payload.html || "<p class='muted-text'>No preview available.</p>";
      if (!isUploading) {
        setStatus("Preview synced");
      }
    } catch (_error) {
      if (!isUploading) {
        setStatus("Preview failed");
      }
    }
  }, 180);

  textarea.addEventListener("input", renderPreview);
  renderPreview();
}

function setupMarkdownReader() {
  const readerRoot = document.querySelector("[data-markdown-reader]");
  if (!readerRoot) {
    return;
  }

  const article = readerRoot.querySelector(".markdown-body");
  const outline = readerRoot.querySelector("[data-reader-outline]");
  if (!article || !outline) {
    return;
  }

  const headings = article.querySelectorAll("h1, h2, h3");
  if (!headings.length) {
    outline.innerHTML = "<p class='muted-text'>No headings in this document.</p>";
    return;
  }

  const list = document.createElement("ul");
  list.className = "reader-outline";

  headings.forEach((heading, index) => {
    const id = heading.id || `section-${index + 1}`;
    heading.id = id;

    const item = document.createElement("li");
    item.className = `reader-outline__item reader-outline__item--${heading.tagName.toLowerCase()}`;

    const link = document.createElement("a");
    link.href = `#${id}`;
    link.textContent = heading.textContent || `Section ${index + 1}`;

    item.appendChild(link);
    list.appendChild(item);
  });

  outline.innerHTML = "";
  outline.appendChild(list);
}

document.addEventListener("DOMContentLoaded", () => {
  setupMarkdownEditor();
  setupMarkdownReader();
});
