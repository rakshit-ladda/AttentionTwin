import type {
  CounterfactualCompareRequest,
  CounterfactualCompareResponse,
  EventHistoryResponse,
  HealthResponse,
  ModelStatusResponse,
  NotificationEventCreate,
  NotificationEventResponse,
} from '../api';

const EVENTS_KEY = 'attentiontwin_offline_events_v1';

function readEvents(): NotificationEventResponse[] {
  try {
    const raw = localStorage.getItem(EVENTS_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? (parsed as NotificationEventResponse[]) : [];
  } catch {
    return [];
  }
}

function writeEvents(events: NotificationEventResponse[]): void {
  localStorage.setItem(EVENTS_KEY, JSON.stringify(events.slice(0, 500)));
}

export const offlineHealth = (): HealthResponse => ({
  status: 'healthy',
  service: 'AttentionTwin on-device runtime',
  version: 'offline-rules-v1',
  environment: 'on-device / offline',
  timestamp: new Date().toISOString(),
});

export const offlineModelStatus = (): ModelStatusResponse => ({
  model_loaded: false,
  model_name: 'On-device safety rules (not a trained ML model)',
  model_version: 'offline-rules-v1',
  training_samples: 0,
  target: 'No personal outcome model is available on this device yet',
  data_provenance: 'Local device only; no personal outcomes have been learned',
});

export function createOfflineEvent(payload: NotificationEventCreate): NotificationEventResponse {
  const events = readEvents();
  const event: NotificationEventResponse = {
    id: Math.max(Date.now(), (events[0]?.id ?? 0) + 1),
    text: '[Message text not stored in offline mode]',
    source_app: payload.source_app,
    category: payload.category,
    timestamp: new Date().toISOString(),
    context_data: payload.context_data,
  };
  writeEvents([event, ...events]);
  return event;
}

export function listOfflineEvents(limit = 50, offset = 0): NotificationEventResponse[] {
  return readEvents().slice(offset, offset + limit);
}

export function getOfflineEventHistory(eventId: number): EventHistoryResponse {
  const event = readEvents().find((item) => item.id === eventId);
  if (!event) throw new Error('This event is not in the on-device history.');
  return {
    event,
    decisions: [],
    observed_outcomes: [],
    counterfactual_predictions: [],
    feedback: [],
  };
}

const IMPORTANT_CATEGORIES = new Set([
  'system', 'system_alert', 'finance', 'health', 'calendar_reminder', 'alert',
  'cpu_spike', 'build_failure', 'service_outage', 'emergency',
]);

/**
 * Conservative on-device policy for offline operation. It does not claim to
 * predict a user's behavior: this device currently has no labeled outcomes.
 */
export function compareOffline(request: CounterfactualCompareRequest): CounterfactualCompareResponse {
  const category = `${request.app_category} ${request.notification_category}`.toLowerCase();
  const important = [...IMPORTANT_CATEGORIES].some((value) => category.includes(value));
  const focused = request.is_focus_session === 1 || ['deep_work', 'meeting'].includes(request.focus_mode);
  const recommended = important || !focused ? 'allow' : 'defer';
  const rationale = important
    ? 'Conservative offline rule: keep system, health, finance, and urgent alerts available immediately.'
    : focused
      ? 'Conservative offline rule: defer a non-urgent alert during a declared focus session; the user must confirm the action.'
      : 'Conservative offline rule: allow the alert because no active focus session was declared.';

  const scenarios = (['allow', 'defer', 'suppress'] as const).map((action) => ({
    proposed_action: action,
    predicted_class: -1,
    predicted_label: 'unknown_no_personal_outcomes',
    probability_opened_quickly: null,
    expected_interruption_risk: action === 'allow' ? 'unknown' : 'low',
    timing_explanation: action === 'allow'
      ? 'Immediate delivery. Personal browsing and task-resumption effects are unknown.'
      : action === 'defer'
        ? 'Would defer until the configured break if the user selects Defer. This comparison does not act on the notification.'
        : 'Suppression is shown for comparison only; this app does not automatically suppress other apps’ notifications.',
    support_warning: action === 'suppress'
      ? 'Ordinary Android notification-listener apps cannot reliably suppress another app’s first alert.'
      : undefined,
    estimated_interruption_minutes: action === 'allow' ? null : 0,
    estimated_browsing_minutes: action === 'allow' ? null : 0,
    estimated_resumption_delay_minutes: action === 'allow' ? null : 0,
    deferred_delivery_minutes: null,
    is_recommended: action === recommended,
  }));

  return {
    notification_summary: {
      source_app: request.source_app,
      app_category: request.app_category,
      notification_category: request.notification_category,
      focus_mode: request.focus_mode,
      is_focus_session: request.is_focus_session,
      hour_of_day: request.hour_of_day,
    },
    scenarios,
    relative_comparison_summary: 'Offline mode has no trained personal outcome model. It compares delivery choices qualitatively and does not estimate minutes or opening probabilities.',
    recommended_action: recommended,
    recommendation_rationale: rationale,
    model_version: 'offline-rules-v1 (not ML)',
    data_provenance: 'Computed on this phone. No notification body is sent to a server by this offline path.',
    limitations_disclaimer: 'This is a conservative rule, not a learned personal prediction or causal estimate. The native listener observes notifications after publication. DEFER requires explicit user action; SUPPRESS is not executed.',
  };
}
