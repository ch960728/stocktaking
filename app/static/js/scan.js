const scanInput = document.getElementById("scan-input");
const resultLabel = document.getElementById("scan-result-label");
const logBody = document.getElementById("scan-log-body");
const modeTabs = document.getElementById("scan-mode-tabs");
const cameraToggleBtn = document.getElementById("camera-toggle-btn");
const cameraReaderEl = document.getElementById("camera-reader");
const cameraCaptureBtn = document.getElementById("camera-capture-btn");

let scanMode = "add";

modeTabs.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => {
    scanMode = btn.dataset.mode;
    modeTabs.querySelectorAll("button").forEach((b) => {
      b.className = "btn " + (b.dataset.mode === scanMode ? "btn-primary" : "btn-secondary");
    });
    refocus();
  });
});

function refocus() {
  scanInput.value = "";
  scanInput.focus();
}

function prependLog(action, record, count) {
  if (logBody.querySelector(".empty-row")) logBody.innerHTML = "";
  const tr = document.createElement("tr");
  const time = new Date().toLocaleTimeString("ko-KR", { hour12: false });
  tr.innerHTML = `
    <td>${time}</td>
    <td>${action}</td>
    <td>${record.item.item_name}</td>
    <td>${record.barcode}</td>
    <td class="col-numeric">${count}</td>
  `;
  logBody.prepend(tr);
}

async function currentCount(itemId) {
  const list = await apiRequest("/api/sensor-barcodes" + buildQuery({ item_id: itemId }));
  return list.length;
}

// 물리 스캐너(Enter로 폼 제출)와 카메라 스캔 둘 다 이 함수 하나로 처리한다 --
// 입력 경로만 다르고 이후 로직은 완전히 동일.
async function processScan(barcode) {
  if (!barcode) return;
  try {
    if (scanMode === "add") {
      const record = await apiRequest("/api/sensor-barcodes/scan", {
        method: "POST",
        body: JSON.stringify({ barcode }),
      });
      const count = await currentCount(record.item.id);
      const message = `${record.item.item_name} 바코드 등록 완료 (남은 바코드 ${count}개)`;
      resultLabel.textContent = message;
      showToast(message);
      prependLog("입고", record, count);
    } else {
      const record = await apiRequest("/api/sensor-barcodes/remove", {
        method: "POST",
        body: JSON.stringify({ barcode }),
      });
      const count = await currentCount(record.item.id);
      const message = `${record.item.item_name} 바코드 제거 완료 (남은 바코드 ${count}개)`;
      resultLabel.textContent = message;
      showToast(message);
      prependLog("출고", record, count);
    }
  } catch (err) {
    resultLabel.textContent = "";
    showToast(err.message, "error");
  }
}

document.getElementById("scan-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const barcode = scanInput.value.trim();
  await processScan(barcode);
  refocus();
});

// --- 카메라 스캔 ---

let html5QrCode = null;
let armed = false; // true 사이에 디코딩된 첫 바코드만 실제로 처리한다 (버튼으로 직접 제어)

function cameraSupported() {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) && typeof Html5Qrcode !== "undefined";
}

function requestCapture() {
  if (!html5QrCode) return;
  armed = true;
  resultLabel.textContent = "바코드를 카메라에 비춰주세요...";
}

async function onCameraDecoded(decodedText) {
  // 카메라는 계속 프레임을 디코딩하지만, "스캔하기" 버튼을 눌러 armed 상태가
  // 됐을 때 잡힌 바코드 하나만 실제로 처리한다 -- 그 전까지는 전부 무시.
  // 스캔 간격이 너무 좁다는 피드백으로 "계속 자동 스캔"에서 "버튼 누를 때만
  // 스캔"으로 바꾼 것.
  if (!armed) return;
  armed = false;
  await processScan(decodedText);
}

async function startCamera() {
  if (!cameraSupported()) {
    if (location.protocol !== "https:" && location.hostname !== "localhost") {
      showToast("카메라는 보안 연결(HTTPS)에서만 사용할 수 있습니다. 현재 http로 접속되어 있어 카메라를 열 수 없습니다.", "error");
    } else {
      showToast("이 브라우저에서는 카메라 스캔을 지원하지 않습니다.", "error");
    }
    return;
  }
  cameraReaderEl.hidden = false;
  cameraCaptureBtn.hidden = false;
  cameraToggleBtn.textContent = "카메라 끄기";
  html5QrCode = new Html5Qrcode("camera-reader");
  try {
    await html5QrCode.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 200 } },
      onCameraDecoded,
      () => {} // 매 프레임 디코딩 실패는 정상적인 상황이라 무시
    );
    resultLabel.textContent = "바코드를 비추고 \"스캔하기\"를 눌러주세요.";
  } catch (err) {
    showToast("카메라를 시작할 수 없습니다: " + err, "error");
    await stopCamera();
  }
}

async function stopCamera() {
  if (html5QrCode) {
    try {
      await html5QrCode.stop();
      html5QrCode.clear();
    } catch (err) {
      // 이미 멈춰있는 등 정리 과정의 에러는 무시
    }
    html5QrCode = null;
  }
  armed = false;
  cameraReaderEl.hidden = true;
  cameraCaptureBtn.hidden = true;
  cameraToggleBtn.textContent = "카메라로 스캔";
}

cameraToggleBtn.addEventListener("click", () => {
  if (html5QrCode) {
    stopCamera();
  } else {
    startCamera();
  }
});

cameraCaptureBtn.addEventListener("click", requestCapture);

window.addEventListener("pagehide", stopCamera);

refocus();
