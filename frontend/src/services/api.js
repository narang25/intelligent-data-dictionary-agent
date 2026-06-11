// Extended API client for JARVIS v2.0 — AI Data Catalog
const BASE_URL = import.meta.env.VITE_API_URL || "/api";
const V1 = `${BASE_URL.replace(/\/api$/, "")}/api/v1`;

function getHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

async function request(url, options = {}) {
  const res = await fetch(url, { ...options, headers: getHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

// =========================
// Auth
// =========================
export async function signupUser(email, password) {
  const res = await fetch(`${BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail);
  return data;
}

export async function loginUser(email, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail);
  return data;
}

// =========================
// Chat
// =========================
export async function sendMessageToAPI(question, sessionId = null, connectionId = null) {
  return request(`${BASE_URL}/chat`, {
    method: "POST",
    body: JSON.stringify({ question, session_id: sessionId, connection_id: connectionId }),
  });
}

// =========================
// Connections
// =========================
export async function createConnection(data) {
  return request(`${V1}/connections`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listConnections() {
  return request(`${V1}/connections`);
}

export async function getConnection(id) {
  return request(`${V1}/connections/${id}`);
}

export async function deleteConnection(id) {
  return request(`${V1}/connections/${id}`, { method: "DELETE" });
}

export async function testConnection(data) {
  return request(`${V1}/connections/test`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function syncConnection(id) {
  return request(`${V1}/connections/${id}/sync`, { method: "POST" });
}

// =========================
// Dashboard
// =========================
export async function getOverview(connectionId) {
  return request(`${V1}/connections/${connectionId}/overview`);
}

// =========================
// Tables
// =========================
export async function listTables(connectionId, search = "", page = 1) {
  const params = new URLSearchParams({ search, page, per_page: 50 });
  return request(`${V1}/connections/${connectionId}/tables?${params}`);
}

export async function getTableDetail(connectionId, tableName) {
  return request(`${V1}/connections/${connectionId}/tables/${tableName}`);
}

export async function getSampleData(connectionId, tableName, limit = 20, offset = 0) {
  const params = new URLSearchParams({ limit, offset });
  return request(`${V1}/connections/${connectionId}/tables/${tableName}/sample?${params}`);
}

// =========================
// AI Analysis
// =========================
export async function analyzeDatabase(connectionId, forceRefresh = false, enhanced = false) {
  return request(`${V1}/connections/${connectionId}/ai/analyze`, {
    method: "POST",
    body: JSON.stringify({ force_refresh: forceRefresh, enhanced }),
  });
}

export async function analyzeTable(connectionId, tableName, forceRefresh = false) {
  return request(`${V1}/connections/${connectionId}/tables/${tableName}/ai/analyze`, {
    method: "POST",
    body: JSON.stringify({ force_refresh: forceRefresh }),
  });
}

export async function triggerBatchDocs(connectionId) {
  return request(`${V1}/connections/${connectionId}/ai/generate-docs`, { method: "POST" });
}

export async function getBatchDocsStatus(connectionId) {
  return request(`${V1}/connections/${connectionId}/ai/generate-docs/status`);
}

// =========================
// Quality
// =========================
export async function getQualityScores(connectionId) {
  return request(`${V1}/connections/${connectionId}/quality`);
}

export async function analyzeQuality(connectionId) {
  return request(`${V1}/connections/${connectionId}/quality/analyze`, { method: "POST" });
}

// =========================
// Export
// =========================
export async function createExport(connectionId, format) {
  return request(`${V1}/connections/${connectionId}/export`, {
    method: "POST",
    body: JSON.stringify({ format }),
  });
}

export async function previewExport(connectionId, format = "json") {
  const params = new URLSearchParams({ format });
  return request(`${V1}/connections/${connectionId}/export/preview?${params}`);
}

export function getExportDownloadUrl(jobId) {
  const token = localStorage.getItem("token");
  return `${V1}/export/${jobId}/download?token=${token}`;
}

// =========================
// Explain SQL
// =========================
export async function explainSQL(sql) {
  return request(`${V1}/explain`, {
    method: "POST",
    body: JSON.stringify({ sql }),
  });
}

// =========================
// Annotations (Feature 6)
// =========================
export async function listAnnotations(tableName = null, columnName = null) {
  const params = new URLSearchParams();
  if (tableName) params.set("table_name", tableName);
  if (columnName) params.set("column_name", columnName);
  return request(`${V1}/annotations?${params}`);
}

export async function createAnnotation(tableName, columnName, content) {
  return request(`${V1}/annotations`, {
    method: "POST",
    body: JSON.stringify({ table_name: tableName, column_name: columnName, content }),
  });
}

export async function updateAnnotation(id, content) {
  return request(`${V1}/annotations/${id}`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

export async function deleteAnnotation(id) {
  return request(`${V1}/annotations/${id}`, { method: "DELETE" });
}

// =========================
// Lineage (Feature 2)
// =========================
export async function getLineage(table, column) {
  return request(`${V1}/lineage/${table}/${column}`);
}

export async function getAllLineage(connectionId = null) {
  const url = connectionId ? `${V1}/lineage?connection_id=${connectionId}` : `${V1}/lineage`;
  return request(url);
}

export async function createLineage(data) {
  return request(`${V1}/lineage`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteLineage(id) {
  return request(`${V1}/lineage/${id}`, {
    method: "DELETE",
  });
}

// =========================
// Alerts (Feature 3)
// =========================
export async function listAlerts(activeOnly = true) {
  const params = new URLSearchParams({ active_only: activeOnly });
  return request(`${V1}/alerts?${params}`);
}

export async function dismissAlert(alertId) {
  return request(`${V1}/alerts/${alertId}/dismiss`, { method: "POST" });
}

// =========================
// Permissions / Guardrails (Feature 7)
// =========================
export async function listPermissions(role = null) {
  const params = new URLSearchParams();
  if (role) params.set("role", role);
  return request(`${V1}/permissions?${params}`);
}

export async function getRestrictedColumns() {
  return request(`${V1}/permissions/restricted-columns`);
}

export async function createPermission(data) {
  return request(`${V1}/permissions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deletePermission(permId) {
  return request(`${V1}/permissions/${permId}`, { method: "DELETE" });
}
