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
  const status = editorRoot.querySelector("[data-markdown-status]");
  const previewUrl = editorRoot.dataset.previewUrl;

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

  const renderPreview = debounce(async () => {
    if (!previewUrl) {
      return;
    }

    status.textContent = "Rendering preview...";
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
      status.textContent = "Preview synced";
    } catch (_error) {
      status.textContent = "Preview failed";
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
