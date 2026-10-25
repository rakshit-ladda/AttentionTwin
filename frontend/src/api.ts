/**
 * AttentionTwin API Client
 * Typed wrappers around all backend REST endpoints.
 * All requests go through the Vite proxy at /api/*.
 */

// ── Types ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface NotificationEventCreate {
  text: string;
  source_app: string;
  category: string;
  context_data?: Record<string, unknown>;
}

export interface NotificationEventResponse {
  id: number;
  text: string;
  source_app: string;
  category: string;
  timestamp: string;
  context_data?: Record<string, unknown>;
}

export interface NotificationDecisionResponse {
  id: number;
  event_id: number;
  action: string;
  reason?: string;
  timestamp: string;
}

export interface ObservedOutcomeResponse {
  id: number;
  event_id: number;
  outcome_type: string;
  interaction_measurements?: Record<string, unknown>;
  timestamp: string;
}

export interface CounterfactualPredictionRecord {
  id: number;
  event_id: number;
  proposed_action: string;
  predicted_outcome: Record<string, unknown>;
  model_version: string;
  timestamp: string;
}

export interface UserFeedbackResponse {
  id: number;
  event_id: number;
  feedback_rating?: number;
  feedback_label?: string;
  comment?: string;
  timestamp: string;
}

export interface EventHistoryResponse {
  event: NotificationEventResponse;
  decisions: NotificationDecisionResponse[];
  observed_outcomes: ObservedOutcomeResponse[];
  counterfactual_predictions: CounterfactualPredictionRecord[];
  feedback: UserFeedbackResponse[];
}

// ── Counterfactual types ───────────────────────────────────────────────────

export interface CounterfactualCompareRequest {
  source_app: string;
  app_category: string;
  notification_category: string;
  text_length: number;
  hour_of_day: number;
  day_of_week: number;
  is_weekend: number;
  focus_mode: string;
  is_focus_session: number;
  recent_notification_count_15m?: number;
  minutes_since_last_notification?: number;
  notification_load_1h?: number;
  app_historical_open_rate?: number;
  app_historical_ignore_rate?: number;
  user_historical_open_rate?: number;
  recent_allow_rate_1h?: number;
  recent_suppress_rate_1h?: number;
}

export interface CounterfactualScenarioResult {
  proposed_action: string;
  predicted_class: number;
  predicted_label: string;
  probability_opened_quickly: number;
  expected_interruption_risk: string;
  timing_explanation: string;
  support_warning?: string;
}

export interface CounterfactualCompareResponse {
  notification_summary: Record<string, unknown>;
  scenarios: CounterfactualScenarioResult[];
  relative_comparison_summary: string;
  model_version: string;
  data_provenance: string;
  limitations_disclaimer: string;
}

// ── ML Model Status ────────────────────────────────────────────────────────

export interface ModelStatusResponse {
  model_loaded: boolean;
  model_name?: string;
  model_version?: string;
  accuracy?: number;
  roc_auc?: number;
  training_samples?: number;
  feature_count?: number;
  target?: string;
  trained_at?: string;
  data_provenance?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem('attentiontwin_api_base_url');
    if (custom) return custom.trim().replace(/\/+$/, '');
  }
  const envUrl = (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE_URL;
  if (envUrl) return envUrl.trim().replace(/\/+$/, '');
  return '';
}

export function setApiBaseUrl(url: string): void {
  if (typeof window === 'undefined') return;
  const clean = url.trim().replace(/\/+$/, '');
  if (!clean) {
    localStorage.removeItem('attentiontwin_api_base_url');
  } else {
    localStorage.setItem('attentiontwin_api_base_url', clean);
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const fullUrl = baseUrl ? `${baseUrl}${path}` : path;

  try {
    const res = await fetch(fullUrl, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return (await res.json()) as Promise<T>;
  } catch (err: unknown) {
    if (err instanceof TypeError && (err.message.includes('fetch') || err.message.includes('NetworkError') || err.message.includes('Failed'))) {
      const target = baseUrl || 'local Vite proxy (/api)';
      throw new Error(`Cannot connect to backend (${target}). Ensure FastAPI is running on host 0.0.0.0 and your device is on the same network.`);
    }
    throw err;
  }
}

// ── API functions ──────────────────────────────────────────────────────────

export const api = {
  /** Phase 1 */
  health: () => apiFetch<HealthResponse>('/api/health'),

  /** Phase 2 — Events */
  createEvent: (payload: NotificationEventCreate) =>
    apiFetch<NotificationEventResponse>('/api/events', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listEvents: (limit = 50, offset = 0) =>
    apiFetch<NotificationEventResponse[]>(`/api/events?limit=${limit}&offset=${offset}`),

  getEventHistory: (eventId: number) =>
    apiFetch<EventHistoryResponse>(`/api/events/${eventId}/history`),

  /** Phase 4 — Model status */
  modelStatus: () => apiFetch<ModelStatusResponse>('/api/models/status'),

  /** Phase 5 — Counterfactual comparison */
  compareCounterfactuals: (payload: CounterfactualCompareRequest) =>
    apiFetch<CounterfactualCompareResponse>('/api/counterfactuals/compare', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** Mobile / Config helpers */
  getBaseUrl: getApiBaseUrl,
  setBaseUrl: setApiBaseUrl,
};
