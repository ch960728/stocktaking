let selectedItem = null;
let currentStock = null; // manual/바코드없음 portion only -- see note below
let barcodeCount = 0;

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function isSensorTracked() {
  return barcodeCount > 0 || !!(selectedItem && selectedItem.barcode_prefix);
}

function updateSelectedItemUi() {
  const label = document.getElementById("selected-item-label");
  const submitBtn = document.getElementById("submit-btn");
  const quantityLabel = document.getElementById("quantity-label");
  const breakdown = document.getElementById("stock-breakdown");
  if (!selectedItem) {
    label.textContent = "";
    submitBtn.disabled = true;
    quantityLabel.textContent = "수량 *";
    breakdown.hidden = true;
    return;
  }
  submitBtn.disabled = false;
  const sizeText = itemSizeLabel(selectedItem);
  const base = `${selectedItem.item_name}${sizeText ? " [" + sizeText + "]" : ""} (${selectedItem.category.name} / ${selectedItem.unit.name}${selectedItem.location ? " / " + selectedItem.location.name : ""})`;
  if (isSensorTracked()) {
    // 바코드로 추적되는 품목은 "수량" 하나가 아니라 두 부분의 합이다:
    // 바코드로 추적되는 개수(센서 재고 등록에서 관리) + 바코드 없는 개수(이 폼에서 수동 입력).
    // 이 폼의 quantity-input은 항상 "바코드 없는 개수"만 의미한다 -- 전체를 덮어쓰는 값이 아님.
    // 헷갈리기 쉬운 지점이라 한 줄 요약 대신 카드로 세 숫자를 분리해서 보여준다.
    quantityLabel.textContent = "바코드 없는 보유 수량 *";
    label.textContent = `선택된 품목: ${base}`;
    const manual = currentStock ?? 0;
    document.getElementById("breakdown-barcode").textContent = `${barcodeCount}개`;
    document.getElementById("breakdown-manual").textContent = `${manual}개`;
    document.getElementById("breakdown-total").textContent = `${barcodeCount + manual}개`;
    breakdown.hidden = false;
  } else {
    quantityLabel.textContent = "수량 *";
    const stockText = currentStock !== null ? ` / 현재고 ${currentStock}` : "";
    label.textContent = `선택된 품목: ${base}${stockText}`;
    breakdown.hidden = true;
  }
}

async function selectItem(item) {
  selectedItem = item;
  document.getElementById("item-search-input").value = item.item_name;
  // 구분/위치는 품목 등록 데이터가 기준 -- 선택된 품목의 실제 값으로 맞춘다
  // (사전에 필터로 좁혀뒀더라도, 선택 후에는 그 품목의 진짜 값을 그대로 보여준다).
  document.getElementById("filter-category").value = item.category.id;
  document.getElementById("filter-location").value = item.location ? item.location.id : "";
  try {
    const res = await apiRequest(`/api/stocktakes/latest/${item.id}`);
    currentStock = res.quantity ?? 0;
  } catch (err) {
    currentStock = 0;
  }
  try {
    const list = await apiRequest("/api/sensor-barcodes" + buildQuery({ item_id: item.id }));
    barcodeCount = list.length;
  } catch (err) {
    barcodeCount = 0;
  }
  document.getElementById("quantity-input").value = currentStock;
  updateSelectedItemUi();
}

function clearSelectedItem() {
  selectedItem = null;
  currentStock = null;
  barcodeCount = 0;
  document.getElementById("quantity-input").value = "";
  updateSelectedItemUi();
}

function setupItemAutocomplete() {
  attachAutocomplete({
    inputEl: document.getElementById("item-search-input"),
    listEl: document.getElementById("item-search-autocomplete"),
    showOnFocus: true,
    fetchItems: (q) =>
      apiRequest(
        "/api/items" +
          buildQuery({
            search: q,
            category_id: document.getElementById("filter-category").value,
            location_id: document.getElementById("filter-location").value,
            limit: 20,
          })
      ),
    renderLabel: (item) => item.item_name,
    renderMeta: (item) =>
      [
        itemSizeLabel(item) ? `규격 ${itemSizeLabel(item)}` : null,
        item.item_no ? `품번 ${item.item_no}` : null,
        item.category.name,
        item.unit.name,
        item.location ? item.location.name : null,
      ]
        .filter(Boolean)
        .join(" / "),
    onSelect: (item) => selectItem(item),
  });

  document.getElementById("item-search-input").addEventListener("input", () => {
    clearSelectedItem();
  });
}

async function initSelects() {
  const [categories, locations] = await Promise.all([
    loadCodeGroup("CATEGORY"),
    loadCodeGroup("LOCATION"),
  ]);
  populateSelect(document.getElementById("filter-category"), categories);
  populateSelect(document.getElementById("filter-location"), locations);
  populateSelect(document.getElementById("list-filter-category"), categories);
}

async function loadStocktakes() {
  const params = {
    search: document.getElementById("search-input").value.trim(),
    category_id: document.getElementById("list-filter-category").value,
    date_from: document.getElementById("date-from-input").value,
    date_to: document.getElementById("date-to-input").value,
    limit: 100,
  };
  const records = await apiRequest("/api/stocktakes" + buildQuery(params));
  renderStocktakeTable(records);
}

function renderStocktakeTable(records) {
  const tbody = document.getElementById("stocktake-table-body");
  tbody.innerHTML = "";
  if (!records.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="10">등록된 재고조사 기록이 없습니다</td></tr>';
    return;
  }
  records.forEach((r) => tbody.appendChild(renderStocktakeRow(r)));
}

function renderStocktakeRow(r) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${r.item.item_name}</td>
    <td>${r.item.item_no ?? ""}</td>
    <td>${itemSizeLabel(r.item)}</td>
    <td>${r.item.category.name}</td>
    <td>${r.item.unit.name}</td>
    <td>${r.item.location ? r.item.location.name : ""}</td>
    <td class="col-numeric">${r.quantity}</td>
    <td>${r.survey_date}</td>
    <td>${r.note ?? ""}</td>
    <td></td>
  `;
  const actionTd = tr.lastElementChild;

  const editBtn = document.createElement("button");
  editBtn.className = "btn btn-secondary btn-small";
  editBtn.textContent = "수정";
  editBtn.addEventListener("click", () => tr.replaceWith(renderStocktakeEditRow(r)));
  actionTd.appendChild(editBtn);

  const delBtn = document.createElement("button");
  delBtn.className = "btn btn-danger btn-small";
  delBtn.textContent = "삭제";
  delBtn.style.marginLeft = "4px";
  delBtn.addEventListener("click", () => deleteStocktake(r));
  actionTd.appendChild(delBtn);
  return tr;
}

function renderStocktakeEditRow(r) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${r.item.item_name}</td>
    <td>${r.item.item_no ?? ""}</td>
    <td>${itemSizeLabel(r.item)}</td>
    <td>${r.item.category.name}</td>
    <td>${r.item.unit.name}</td>
    <td>${r.item.location ? r.item.location.name : ""}</td>
    <td><input type="number" step="0.01" class="edit-quantity" value="${r.quantity}" style="width:80px"></td>
    <td><input type="date" class="edit-date" value="${r.survey_date}"></td>
    <td><input type="text" class="edit-note" value="${r.note ?? ""}" maxlength="500"></td>
    <td></td>
  `;
  const actionTd = tr.lastElementChild;

  const saveBtn = document.createElement("button");
  saveBtn.className = "btn btn-primary btn-small";
  saveBtn.textContent = "저장";
  saveBtn.addEventListener("click", () => saveStocktakeEdit(tr, r));
  const cancelBtn = document.createElement("button");
  cancelBtn.className = "btn btn-secondary btn-small";
  cancelBtn.textContent = "취소";
  cancelBtn.style.marginLeft = "4px";
  cancelBtn.addEventListener("click", () => tr.replaceWith(renderStocktakeRow(r)));
  actionTd.appendChild(saveBtn);
  actionTd.appendChild(cancelBtn);
  return tr;
}

async function saveStocktakeEdit(tr, r) {
  const payload = {
    quantity: Number(tr.querySelector(".edit-quantity").value),
    survey_date: tr.querySelector(".edit-date").value,
    note: tr.querySelector(".edit-note").value.trim() || null,
  };
  try {
    await apiRequest(`/api/stocktakes/${r.id}`, { method: "PUT", body: JSON.stringify(payload) });
    showToast("재고조사 기록이 수정되었습니다");
    loadStocktakes();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteStocktake(r) {
  if (!confirm(`'${r.item.item_name}' 재고조사 기록을 삭제하시겠습니까?`)) return;
  try {
    await apiRequest(`/api/stocktakes/${r.id}`, { method: "DELETE" });
    showToast("재고조사 기록이 삭제되었습니다");
    loadStocktakes();
  } catch (err) {
    showToast(err.message, "error");
  }
}

document.getElementById("stocktake-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedItem) return;
  const payload = {
    item_id: selectedItem.id,
    quantity: Number(document.getElementById("quantity-input").value),
    survey_date: document.getElementById("survey-date-input").value,
    note: document.getElementById("note-input").value.trim() || null,
  };
  try {
    await apiRequest("/api/stocktakes", { method: "POST", body: JSON.stringify(payload) });
    showToast("재고조사 기록이 추가되었습니다");
    document.getElementById("item-search-input").value = "";
    document.getElementById("note-input").value = "";
    document.getElementById("survey-date-input").value = todayIso();
    clearSelectedItem();
    loadStocktakes();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("filter-category").addEventListener("change", clearSelectedItem);
document.getElementById("filter-location").addEventListener("change", clearSelectedItem);

document.getElementById("search-input").addEventListener("input", debounce(loadStocktakes, 250));
document.getElementById("list-filter-category").addEventListener("change", loadStocktakes);
document.getElementById("date-from-input").addEventListener("change", loadStocktakes);
document.getElementById("date-to-input").addEventListener("change", loadStocktakes);

(async function init() {
  document.getElementById("survey-date-input").value = todayIso();
  await initSelects();
  setupItemAutocomplete();
  updateSelectedItemUi();
  await loadStocktakes();
})();
