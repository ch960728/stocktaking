function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `요청이 실패했습니다 (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch (_) {
      // ignore body parse failure
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

function debounce(fn, delay = 250) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      query.set(key, value);
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

const commonCodeCache = {}; // group_code -> [{id, code, name}]

async function loadCodeGroup(groupCode) {
  if (!commonCodeCache[groupCode]) {
    commonCodeCache[groupCode] = await apiRequest(
      "/api/common-codes" + buildQuery({ group_code: groupCode })
    );
  }
  return commonCodeCache[groupCode];
}

function populateSelect(selectEl, codes) {
  codes.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name;
    selectEl.appendChild(opt);
  });
}

// 규격상세(폭x길이x높이)만 "5 x 20 x 3" 형태로. 셋 다 비어있으면 빈 문자열.
function sizeDetailText(item) {
  const parts = [item.size_width, item.size_length, item.size_height].map((v) =>
    v === null || v === undefined ? "-" : v
  );
  return parts.some((v) => v !== "-") ? parts.join(" x ") : "";
}

// 규격약식(소/중/대)과 규격상세를 합쳐 한 줄로 -- 동일 품목명이라도 규격이
// 다른 품목을 자동완성/선택 목록에서 구분할 수 있게 어디서나 같은 형식으로 쓴다.
function itemSizeLabel(item) {
  const abbr = item.size_abbr ? item.size_abbr.name : "";
  const detail = sizeDetailText(item);
  if (abbr && detail) return `${abbr}(${detail})`;
  return abbr || detail || "";
}
