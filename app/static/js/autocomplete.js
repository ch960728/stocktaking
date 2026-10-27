function attachAutocomplete({ inputEl, listEl, fetchItems, onSelect, renderLabel, renderMeta, showOnFocus = false }) {
  let items = [];
  let focusedIndex = -1;

  function close() {
    listEl.classList.remove("is-open");
    listEl.innerHTML = "";
    items = [];
    focusedIndex = -1;
  }

  function updateFocus() {
    Array.from(listEl.children).forEach((el, idx) => {
      el.classList.toggle("is-focused", idx === focusedIndex);
    });
  }

  function select(idx) {
    const item = items[idx];
    if (!item) return;
    onSelect(item);
    close();
  }

  function render() {
    if (!items.length) {
      close();
      return;
    }
    listEl.innerHTML = "";
    items.forEach((item, idx) => {
      const row = document.createElement("div");
      row.className = "autocomplete-item";
      const label = document.createElement("div");
      label.textContent = renderLabel(item);
      row.appendChild(label);
      if (renderMeta) {
        const meta = document.createElement("div");
        meta.className = "autocomplete-item__meta";
        meta.textContent = renderMeta(item);
        row.appendChild(meta);
      }
      row.addEventListener("mousedown", (e) => {
        e.preventDefault();
        select(idx);
      });
      listEl.appendChild(row);
    });
    listEl.classList.add("is-open");
  }

  const fetchDebounced = debounce(async (query) => {
    if (!query && !showOnFocus) {
      close();
      return;
    }
    items = await fetchItems(query);
    render();
  }, 250);

  inputEl.addEventListener("input", () => fetchDebounced(inputEl.value.trim()));
  if (showOnFocus) {
    // combobox behavior: show the (filtered) list immediately on focus,
    // not just once the user starts typing.
    inputEl.addEventListener("focus", () => fetchDebounced(inputEl.value.trim()));
  }
  inputEl.addEventListener("blur", () => setTimeout(close, 100));
  inputEl.addEventListener("keydown", (e) => {
    if (!listEl.classList.contains("is-open")) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      focusedIndex = Math.min(focusedIndex + 1, items.length - 1);
      updateFocus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      focusedIndex = Math.max(focusedIndex - 1, 0);
      updateFocus();
    } else if (e.key === "Enter") {
      if (focusedIndex >= 0) {
        e.preventDefault();
        select(focusedIndex);
      }
    } else if (e.key === "Escape") {
      close();
    }
  });

  return { close };
}
