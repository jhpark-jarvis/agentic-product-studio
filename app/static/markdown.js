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
  const imageInput = editorRoot.querySelector("[data-md-image-input]");
  const status = editorRoot.querySelector("[data-markdown-status]");
  const documentId = editorRoot.dataset.documentId || "";
  const draftKey = editorRoot.dataset.draftKey || "";
  const previewUrl = editorRoot.dataset.previewUrl;
  const formatUrl = editorRoot.dataset.formatUrl;
  const uploadUrl = editorRoot.dataset.uploadUrl;
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
