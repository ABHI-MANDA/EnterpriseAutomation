const API_BASE = '/api/v1';

export async function fetchWithAuth(endpoint: string, token: string, options: RequestInit = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...(options.headers || {})
  };
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) {
    throw new Error('Unauthorized');
  }
  return res;
}

export async function getOverview(token: string, region?: string) {
  const q = region ? `?region=${encodeURIComponent(region)}` : '';
  const res = await fetchWithAuth(`/analytics/overview${q}`, token);
  return res.json();
}

export async function getLeads(token: string, params: Record<string, any>) {
  const query = new URLSearchParams(params).toString();
  const res = await fetchWithAuth(`/records/leads?${query}`, token);
  return res.json();
}

export async function previewAllocations(token: string, leadIds: string[]) {
  const res = await fetchWithAuth('/crm-operations/assignments/preview', token, {
    method: 'POST',
    body: JSON.stringify({ lead_ids: leadIds, strategy: 'auto_workload' })
  });
  return res.json();
}

export async function executeAllocations(token: string, batchId: string, approved: boolean) {
  const res = await fetchWithAuth('/crm-operations/assignments/execute', token, {
    method: 'POST',
    body: JSON.stringify({
      batch_id: batchId,
      idempotency_key: `IDEMP-FE-${batchId}`,
      approved
    })
  });
  return res.json();
}

export async function askAIAgent(token: string, message: string, contextFilters?: Record<string, any>) {
  const res = await fetchWithAuth('/agents/chat', token, {
    method: 'POST',
    body: JSON.stringify({ message, context_filters: contextFilters })
  });
  return res.json();
}
