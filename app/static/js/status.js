async function initSelects() {
  const [categories, locations] = await Promise.all([
    loadCodeGroup("CATEGORY"),
    loadCodeGroup("LOCATION"),
  ]);
  populateSelect(document.getElementById("filter-category"), categories);
  populateSelect(document.getElementById("filter-location"), locations);
}

async function loadStatus() {
  const params = {
    search: document.getElementById("search-input").value.trim(),
    category_id: document.getElementById("filter-category").value,
    location_id: document.getElementById("filter-location").value,
    limit: 200,
  };
  const rows = await apiRequest("/api/stocktakes/status" + buildQuery(params));
  renderStatusTable(rows);
}

const STATUS_COLUMNS = 10;

function renderStatusTable(rows) {
  const tbody = document.getElementById("status-table-body");
  tbody.innerHTML = "";
  if (!rows.length) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="${STATUS_COLUMNS}">표시할 품목이 없습니다</td></tr>`;
    return;
  }
  rows.forEach((row) => renderStatusRow(row).forEach((tr) => tbody.appendChild(tr)));
}

function renderStatusRow(row) {
  const item = row.item;
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${item.item_name}</td>
    <td>${item.item_no ?? ""}</td>
    <td>${item.category.name}</td>
    <td>${item.unit.name}</td>
    <td>${item.location ? item.location.name : ""}</td>
    <td>${item.size_abbr ? item.size_abbr.name : ""}</td>
    <td class="col-numeric">${row.current_stock ?? "-"}</td>
    <td class="col-numeric">${row.last_quantity ?? "-"}</td>
    <td>${row.last_survey_date ?? "-"}</td>
    <td></td>
  `;
  const barcodeTd = tr.lastElementChild;

  if (!row.barcode_count) {
    // show "0" only for items actually under barcode tracking; leave
    // ordinary items blank. Gate on the count itself, not on whether
    // barcode_prefix is still set -- a count can outlive a cleared prefix
    // (e.g. registered sensors stay registered if the item's prefix is
    // edited afterwards), and this must stay visible either way.
    barcodeTd.textContent = item.barcode_prefix ? "0" : "";
    return [tr];
  }

  const detailRow = document.createElement("tr");
  const detailTd = document.createElement("td");
  detailTd.colSpan = STATUS_COLUMNS;
  detailTd.className = "autocomplete-item__meta";
  detailRow.appendChild(detailTd);
  detailRow.style.display = "none";

  const toggleBtn = document.createElement("button");
  toggleBtn.className = "btn btn-secondary btn-small";
  toggleBtn.textContent = `${row.barcode_count}건 보기`;

  async function renderDetail() {
    const list = await apiRequest("/api/sensor-barcodes" + buildQuery({ item_id: item.id }));
    detailTd.innerHTML = "";
    const label = document.createElement("span");
    label.textContent = "등록된 바코드: ";
    detailTd.appendChild(label);
    list.forEach((b) => {
      const chip = document.createElement("span");
      chip.style.marginRight = "12px";
      chip.textContent = b.barcode + " ";
      const delBtn = document.createElement("button");
      delBtn.className = "btn btn-danger btn-small";
      delBtn.textContent = "제거";
      delBtn.addEventListener("click", async () => {
        if (!confirm(`'${b.barcode}' 바코드를 제거하시겠습니까?`)) return;
        try {
          await apiRequest(`/api/sensor-barcodes/${b.id}`, { method: "DELETE" });
          showToast(`'${b.barcode}' 바코드를 제거했습니다`);
          row.barcode_count -= 1;
          toggleBtn.textContent = `${row.barcode_count}건 숨기기`;
          await renderDetail();
        } catch (err) {
          showToast(err.message, "error");
        }
      });
      chip.appendChild(delBtn);
      detailTd.appendChild(chip);
    });
  }

  toggleBtn.addEventListener("click", async () => {
    const isOpen = detailRow.style.display !== "none";
    if (isOpen) {
      detailRow.style.display = "none";
      toggleBtn.textContent = `${row.barcode_count}건 보기`;
      return;
    }
    await renderDetail();
    detailRow.style.display = "";
    toggleBtn.textContent = `${row.barcode_count}건 숨기기`;
  });
  barcodeTd.appendChild(toggleBtn);

  return [tr, detailRow];
}

document.getElementById("search-input").addEventListener("input", debounce(loadStatus, 250));
document.getElementById("filter-category").addEventListener("change", loadStatus);
document.getElementById("filter-location").addEventListener("change", loadStatus);

(async function init() {
  await initSelects();
  await loadStatus();
})();
