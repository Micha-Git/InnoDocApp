<template>
  <div class="page">
    <header class="header">
      <h1>Secure Token Service</h1>
      <p class="subtitle">Scan the QR code to complete your VP presentation.</p>
    </header>

    <section class="panel">
      <div class="controls">
        <button
          class="btn btn-primary"
          :disabled="isLoading || isPolling"
          @click="startVerification"
        >
          Start Verification
        </button>
        <button
          class="btn btn-secondary"
          :disabled="!isPolling"
          @click="cancelPolling"
        >
          Cancel
        </button>
      </div>

      <div v-if="errorMessage" class="alert alert-error">
        {{ errorMessage }}
      </div>

      <div class="qr-area">
        <div v-if="isLoading" class="status">Requesting QR code...</div>
        <div v-else-if="qrCodeData" class="qr-wrapper">
          <img :src="qrCodeData" alt="VP QR Code" class="qr-image" />
          <div class="status">
            {{ statusMessage }}
          </div>
          <div v-if="isPolling" class="progress-container">
            <div class="progress-bar"></div>
          </div>
        </div>
        <div v-else class="placeholder">
          QR code will appear here after you start verification.
        </div>
      </div>

      <div v-if="jwtToken" class="token-box">
        <div class="token-title">JWT Set</div>
        <div class="token-hint">Token stored in localStorage as jwt_token.</div>
        <textarea readonly class="token-text" :value="jwtToken" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from "vue";

const isLoading = ref(false);
const isPolling = ref(false);
const statusMessage = ref("Waiting for wallet scan...");
const errorMessage = ref("");
const qrCodeData = ref("");
const jwtToken = ref("");
const sessionId = ref("");
const returnUrl = ref(getReturnUrl());

let pollInterval = null;

const startVerification = async () => {
  errorMessage.value = "";
  jwtToken.value = "";
  sessionId.value = "";
  qrCodeData.value = "";
  if (!returnUrl.value) {
    errorMessage.value = "Missing return_url from proxy";
    return;
  }
  statusMessage.value = "Waiting for wallet scan...";
  isLoading.value = true;

  try {
    const response = await fetch("/api/qrcode");
    if (!response.ok) {
      throw new Error(`Failed to request QR code: ${response.statusText}`);
    }
    const data = await response.json();
    const qrUrl = data.qr_url || "";
    sessionId.value = data.session_id || "";
    if (!qrUrl) {
      throw new Error("QR code response missing qr_url");
    }
    if (!sessionId.value) {
      throw new Error("QR code response missing session_id");
    }
    // qr_url is now a base64 data URI from the backend
    qrCodeData.value = qrUrl;
    startPolling();
  } catch (error) {
    errorMessage.value = error.message || "Failed to start verification";
  } finally {
    isLoading.value = false;
  }
};

const startPolling = () => {
  stopPolling();
  isPolling.value = true;
  pollInterval = setInterval(checkStatus, 2000);
};

const checkStatus = async () => {
  try {
    if (!sessionId.value) {
      return;
    }
    const response = await fetch(
      `/api/status?session_id=${encodeURIComponent(sessionId.value)}`,
    );
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    if (data.status === "pending") {
      statusMessage.value = "Waiting for wallet scan...";
    }
    if (data.status === "complete") {
      issueAndRedirect();
    }
  } catch {
    // keep polling
  }
};

const cancelPolling = () => {
  stopPolling();
  isPolling.value = false;
  statusMessage.value = "Verification cancelled.";
  sessionId.value = "";
};

const issueAndRedirect = () => {
  stopPolling();
  isPolling.value = false;
  statusMessage.value = "Issuing token and redirecting...";
  if (!sessionId.value || !returnUrl.value) {
    errorMessage.value = "Missing session or return_url";
    return;
  }
  const target = `/api/issue?session_id=${encodeURIComponent(
    sessionId.value,
  )}&return_url=${encodeURIComponent(returnUrl.value)}`;
  window.location.href = target;
};

function getReturnUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("return_url") || "";
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
};

onBeforeUnmount(() => {
  stopPolling();
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7f5f0 0%, #eef2f7 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 60px;
  color: #1f2937;
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.4rem;
  margin: 0 0 10px 0;
}

.subtitle {
  margin: 0;
  color: #4b5563;
}

.panel {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  width: min(800px, 95vw);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
}

.controls {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.btn {
  border: none;
  border-radius: 10px;
  padding: 12px 18px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #0f766e;
  color: #ffffff;
  box-shadow: 0 10px 20px rgba(15, 118, 110, 0.25);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-secondary {
  background: #e5e7eb;
  color: #111827;
}

.qr-area {
  border: 1px dashed #cbd5f5;
  border-radius: 12px;
  padding: 20px;
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
}

.qr-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qr-image {
  width: 220px;
  height: 220px;
  border: 10px solid #111827;
  border-radius: 12px;
  background: #ffffff;
}

.status {
  font-size: 0.95rem;
  color: #0f172a;
}

.placeholder {
  color: #6b7280;
}

.alert {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 8px;
}

.alert-error {
  background: #fee2e2;
  color: #991b1b;
}

.token-box {
  margin-top: 20px;
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 12px;
}

.token-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.token-hint {
  font-size: 0.85rem;
  margin-bottom: 10px;
  color: #94a3b8;
}

.token-text {
  width: 100%;
  min-height: 120px;
  background: #0b1120;
  color: #e2e8f0;
  border: 1px solid #1e293b;
  border-radius: 8px;
  padding: 10px;
  font-size: 0.85rem;
  font-family: "Courier New", monospace;
}

.progress-container {
  width: 100%;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 12px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  animation: indeterminate 1.5s infinite;
}

@keyframes indeterminate {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@media (max-width: 600px) {
  .controls {
    flex-direction: column;
  }

  .qr-image {
    width: 180px;
    height: 180px;
  }
}
</style>
