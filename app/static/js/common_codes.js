const state = { groups: [], activeGroup: null };

async function loadGroups() {
  state.groups = await apiRequest("/api/common-codes/groups");
  if (state.groups.length) {
    state.activeGroup = state.groups[0].group_code;
  }
  renderTabs();
  await loadCodes();
}

function renderTabs() {
  const container = document.getElementById("group-tabs");
  container.innerHTML = "";
  state.groups.forEach((g) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn " + (g.group_code === state.activeGroup ? "btn-primary" : "btn-secondary");
    btn.textContent = g.group_name;
    btn.addEventListener("click", () => {
      state.activeGroup = g.group_code;
      renderTabs();
      loadCodes();
    });
    container.appendChild(btn);
  });
}

async function loadCodes() {
  if (!state.activeGroup) return;
  const keyword = document.getElementById("keyword-input").value.trim();
  const codes = await apiRequest(
    "/api/common-codes" + buildQuery({ group_code: state.activeGroup, keyword })
  );
  renderTable(codes);
}

function renderTable(codes) {
  const tbody = document.getElementById("code-table-body");
  tbody.innerHTML = "";
  if (!codes.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="4">등록된 코드가 없습니다</td></tr>';
    return;
  }
  codes.forEach((c) => tbody.appendChild(renderRow(c)));
}

function renderRow(c) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${c.code}</td>
    <td>${c.name}</td>
    <td class="col-numeric">${c.sort_order}</td>
    <td></td>
  `;
  const actionTd = tr.lastElementChild;

  const editBtn = document.createElement("button");
  editBtn.className = "btn btn-secondary btn-small";
  editBtn.textContent = "수정";
  editBtn.addEventListener("click", () => tr.replaceWith(renderEditRow(c)));
  actionTd.appendChild(editBtn);

  const delBtn = document.createElement("button");
  delBtn.className = "btn btn-danger btn-small";
  delBtn.textContent = "삭제";
  delBtn.style.marginLeft = "4px";
  delBtn.addEventListener("click", () => deleteCode(c));
  actionTd.appendChild(delBtn);
  return tr;
}

function renderEditRow(c) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input type="text" class="edit-code" value="${c.code}" maxlength="30"></td>
    <td><input type="text" class="edit-name" value="${c.name}" maxlength="50"></td>
    <td><input type="number" class="edit-sort" value="${c.sort_order}"></td>
    <td></td>
  `;
  const actionTd = tr.lastElementChild;
  const codeInput = tr.querySelector(".edit-code");
  const nameInput = tr.querySelector(".edit-name");
  const sortInput = tr.querySelector(".edit-sort");

  const saveBtn = document.createElement("button");
  saveBtn.className = "btn btn-primary btn-small";
  saveBtn.textContent = "저장";
  saveBtn.addEventListener("click", async () => {
    try {
      await apiRequest(`/api/common-codes/${c.id}`, {
        method: "PUT",
        body: JSON.stringify({
          code: codeInput.value.trim(),
          name: nameInput.value.trim(),
          sort_order: Number(sortInput.value) || 0,
        }),
      });
      showToast("코드가 수정되었습니다");
      loadCodes();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
  const cancelBtn = document.createElement("button");
  cancelBtn.className = "btn btn-secondary btn-small";
  cancelBtn.textContent = "취소";
  cancelBtn.style.marginLeft = "4px";
  cancelBtn.addEventListener("click", () => tr.replaceWith(renderRow(c)));

  actionTd.appendChild(saveBtn);
  actionTd.appendChild(cancelBtn);
  return tr;
}

async function deleteCode(c) {
  if (!confirm(`'${c.name}' 코드를 삭제하시겠습니까?`)) return;
  try {
    await apiRequest(`/api/common-codes/${c.id}`, { method: "DELETE" });
    showToast("코드가 삭제되었습니다");
    loadCodes();
  } catch (err) {
    showToast(err.message, "error");
  }
}

document.getElementById("code-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const code = document.getElementById("code-input").value.trim();
  const name = document.getElementById("name-input").value.trim();
  const sortOrder = Number(document.getElementById("sort-order-input").value) || 0;
  try {
    await apiRequest("/api/common-codes", {
      method: "POST",
      body: JSON.stringify({ group_code: state.activeGroup, code, name, sort_order: sortOrder }),
    });
    showToast("코드가 추가되었습니다");
    e.target.reset();
    document.getElementById("sort-order-input").value = 0;
    loadCodes();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("keyword-input").addEventListener("input", debounce(loadCodes, 250));

loadGroups();
