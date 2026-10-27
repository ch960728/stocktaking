async function initSelects() {
  const [categories, units, locations, sizeAbbrs] = await Promise.all([
    loadCodeGroup("CATEGORY"),
    loadCodeGroup("UNIT"),
    loadCodeGroup("LOCATION"),
    loadCodeGroup("SIZE_ABBR"),
  ]);
  populateSelect(document.getElementById("category-select"), categories);
  populateSelect(document.getElementById("unit-select"), units);
  populateSelect(document.getElementById("location-select"), locations);
  populateSelect(document.getElementById("size-abbr-select"), sizeAbbrs);
  populateSelect(document.getElementById("filter-category"), categories);
  populateSelect(document.getElementById("filter-location"), locations);
}

function setupNameAutocomplete() {
  attachAutocomplete({
    inputEl: document.getElementById("item-name-input"),
    listEl: document.getElementById("item-name-autocomplete"),
    fetchItems: (q) => apiRequest("/api/items" + buildQuery({ search: q, limit: 8 })),
    renderLabel: (item) => item.item_name,
    renderMeta: (item) =>
      [
        item.item_no ? `품번 ${item.item_no}` : null,
        item.barcode_prefix ? `바코드구분 ${item.barcode_prefix}` : null,
        item.category.name,
        item.unit.name,
        item.location ? item.location.name : null,
        itemSizeLabel(item) ? `규격 ${itemSizeLabel(item)}` : null,
      ]
        .filter(Boolean)
        .join(" / "),
    onSelect: (item) => {
      // item_no/barcode are per-item identifiers, so they're deliberately
      // NOT copied here -- only the shared classification/size fields are.
      document.getElementById("item-name-input").value = item.item_name;
      document.getElementById("category-select").value = item.category.id;
      document.getElementById("unit-select").value = item.unit.id;
      document.getElementById("location-select").value = item.location ? item.location.id : "";
      document.getElementById("size-abbr-select").value = item.size_abbr ? item.size_abbr.id : "";
      document.getElementById("size-width-input").value = item.size_width ?? "";
      document.getElementById("size-length-input").value = item.size_length ?? "";
      document.getElementById("size-height-input").value = item.size_height ?? "";
    },
  });
}

async function loadItems() {
  const filters = {
    search: document.getElementById("search-input").value.trim(),
    category_id: document.getElementById("filter-category").value,
    location_id: document.getElementById("filter-location").value,
  };
  const [items, totalCount, filteredCount] = await Promise.all([
    apiRequest("/api/items" + buildQuery({ ...filters, limit: 100 })),
    apiRequest("/api/items/count"),
    apiRequest("/api/items/count" + buildQuery(filters)),
  ]);
  renderItemTable(items);
  document.getElementById("item-count-info").textContent =
    `전체 ${totalCount.count}개 · 조회결과 ${filteredCount.count}개`;
}

function renderItemTable(items) {
  const tbody = document.getElementById("item-table-body");
  tbody.innerHTML = "";
  if (!items.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="11">등록된 품목이 없습니다</td></tr>';
    return;
  }
  items.forEach((item) => tbody.appendChild(renderItemRow(item)));
}

function renderItemRow(item) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${item.id}</td>
    <td>${item.item_name}</td>
    <td>${item.item_no ?? ""}</td>
    <td>${item.barcode ?? ""}</td>
    <td>${item.barcode_prefix ?? ""}</td>
    <td>${item.category.name}</td>
    <td>${item.unit.name}</td>
    <td>${item.location ? item.location.name : ""}</td>
    <td>${item.size_abbr ? item.size_abbr.name : ""}</td>
    <td class="col-numeric">${sizeDetailText(item)}</td>
    <td></td>
  `;
  const actionTd = tr.lastElementChild;

  const editBtn = document.createElement("button");
  editBtn.className = "btn btn-secondary btn-small";
  editBtn.textContent = "수정";
  editBtn.addEventListener("click", () => tr.replaceWith(renderItemEditRow(item)));
  actionTd.appendChild(editBtn);

  const delBtn = document.createElement("button");
  delBtn.className = "btn btn-danger btn-small";
  delBtn.textContent = "삭제";
  delBtn.style.marginLeft = "4px";
  delBtn.addEventListener("click", () => deleteItem(item));
  actionTd.appendChild(delBtn);
  return tr;
}

function selectHtml(className, codes, selectedId, allowEmpty) {
  const options = codes
    .map((c) => `<option value="${c.id}" ${String(c.id) === String(selectedId) ? "selected" : ""}>${c.name}</option>`)
    .join("");
  return `<select class="${className}">${allowEmpty ? '<option value="">선택 안함</option>' : ""}${options}</select>`;
}

function renderItemEditRow(item) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${item.id}</td>
    <td><input type="text" class="edit-item-name" value="${item.item_name}" maxlength="200"></td>
    <td><input type="text" class="edit-item-no" value="${item.item_no ?? ""}" maxlength="100" style="width:90px"></td>
    <td><input type="text" class="edit-barcode" value="${item.barcode ?? ""}" maxlength="100" style="width:90px"></td>
    <td><input type="text" class="edit-barcode-prefix" value="${item.barcode_prefix ?? ""}" maxlength="100" style="width:90px"></td>
    <td>${selectHtml("edit-category", commonCodeCache.CATEGORY, item.category.id, false)}</td>
    <td>${selectHtml("edit-unit", commonCodeCache.UNIT, item.unit.id, false)}</td>
    <td>${selectHtml("edit-location", commonCodeCache.LOCATION, item.location ? item.location.id : "", true)}</td>
    <td>${selectHtml("edit-size-abbr", commonCodeCache.SIZE_ABBR, item.size_abbr ? item.size_abbr.id : "", true)}</td>
    <td>
      <input type="number" step="0.01" class="edit-width" value="${item.size_width ?? ""}" style="width:60px">
      <input type="number" step="0.01" class="edit-length" value="${item.size_length ?? ""}" style="width:60px">
      <input type="number" step="0.01" class="edit-height" value="${item.size_height ?? ""}" style="width:60px">
    </td>
    <td></td>
  `;
  const actionTd = tr.lastElementChild;

  const saveBtn = document.createElement("button");
  saveBtn.className = "btn btn-primary btn-small";
  saveBtn.textContent = "저장";
  saveBtn.addEventListener("click", () => saveItemEdit(tr, item));
  const cancelBtn = document.createElement("button");
  cancelBtn.className = "btn btn-secondary btn-small";
  cancelBtn.textContent = "취소";
  cancelBtn.style.marginLeft = "4px";
  cancelBtn.addEventListener("click", () => tr.replaceWith(renderItemRow(item)));
  actionTd.appendChild(saveBtn);
  actionTd.appendChild(cancelBtn);
  return tr;
}

async function saveItemEdit(tr, item) {
  const payload = {
    item_name: tr.querySelector(".edit-item-name").value.trim(),
    item_no: tr.querySelector(".edit-item-no").value.trim() || null,
    barcode: tr.querySelector(".edit-barcode").value.trim() || null,
    barcode_prefix: tr.querySelector(".edit-barcode-prefix").value.trim() || null,
    category_id: Number(tr.querySelector(".edit-category").value),
    unit_id: Number(tr.querySelector(".edit-unit").value),
    location_id: tr.querySelector(".edit-location").value || null,
    size_abbr_id: tr.querySelector(".edit-size-abbr").value || null,
    size_width: tr.querySelector(".edit-width").value || null,
    size_length: tr.querySelector(".edit-length").value || null,
    size_height: tr.querySelector(".edit-height").value || null,
  };
  try {
    await apiRequest(`/api/items/${item.id}`, { method: "PUT", body: JSON.stringify(payload) });
    showToast("품목이 수정되었습니다");
    loadItems();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteItem(item) {
  if (!confirm(`'${item.item_name}' 품목을 삭제하시겠습니까?`)) return;
  try {
    await apiRequest(`/api/items/${item.id}`, { method: "DELETE" });
    showToast("품목이 삭제되었습니다");
    loadItems();
  } catch (err) {
    showToast(err.message, "error");
  }
}

document.getElementById("item-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    item_name: document.getElementById("item-name-input").value.trim(),
    item_no: document.getElementById("item-no-input").value.trim() || null,
    barcode: document.getElementById("barcode-input").value.trim() || null,
    barcode_prefix: document.getElementById("barcode-prefix-input").value.trim() || null,
    category_id: Number(document.getElementById("category-select").value),
    unit_id: Number(document.getElementById("unit-select").value),
    location_id: document.getElementById("location-select").value || null,
    size_abbr_id: document.getElementById("size-abbr-select").value || null,
    size_width: document.getElementById("size-width-input").value || null,
    size_length: document.getElementById("size-length-input").value || null,
    size_height: document.getElementById("size-height-input").value || null,
  };
  try {
    await apiRequest("/api/items", { method: "POST", body: JSON.stringify(payload) });
    showToast("품목이 추가되었습니다");
    e.target.reset();
    loadItems();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("search-input").addEventListener("input", debounce(loadItems, 250));
document.getElementById("filter-category").addEventListener("change", loadItems);
document.getElementById("filter-location").addEventListener("change", loadItems);

(async function init() {
  await initSelects();
  setupNameAutocomplete();
  await loadItems();
})();
