import type {
  CounterfactualCompareRequest,
  CounterfactualCompareResponse,
  EventHistoryResponse,
  HealthResponse,
  ModelStatusResponse,
  NotificationEventCreate,
  NotificationEventResponse,
} from '../api';
import { attentionListener, LocalNotificationEvent } from './attentionListener';

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

function nativeEventNumberId(id: string): number {
  return Number.parseInt(id.slice(0, 8), 16) || 1;
}

function nativeEventAsHistoryItem(item: LocalNotificationEvent): NotificationEventResponse {
  return {
    id: nativeEventNumberId(item.id),
    text: '[Notification text not stored on this device]',
    source_app: item.appLabel || item.packageName,
    category: 'notification',
    timestamp: new Date(item.postedAt).toISOString(),
    context_data: {
      local_notification_id: item.id,
      package_name: item.packageName,
      lifecycle_state: item.state,
      updated_at: item.updatedAt,
      removed_at: item.removedAt,
      deferred_until: item.deferredUntil,
      removal_reason: item.removalReason,
      clearable: item.clearable,
    },
  };
}

async function readNativeEvents(): Promise<LocalNotificationEvent[]> {
  try {
    const { events } = await attentionListener.getEvents();
    return events;
  } catch {
    return [];
  }
}

export async function listOfflineEvents(limit = 50, offset = 0): Promise<NotificationEventResponse[]> {
  const nativeItems = (await readNativeEvents()).map(nativeEventAsHistoryItem);
  return [...readEvents(), ...nativeItems]
    .sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp))
    .slice(offset, offset + limit);
}

export async function getOfflineEventHistory(eventId: number): Promise<EventHistoryResponse> {
  const savedEvent = readEvents().find((item) => item.id === eventId);
  const nativeItem = (await readNativeEvents()).find((item) => nativeEventNumberId(item.id) === eventId);
  const event = savedEvent ?? (nativeItem ? nativeEventAsHistoryItem(nativeItem) : null);
  if (!event) throw new Error('This event is not in the on-device history.');

  const deferredTransition = nativeItem?.transitions?.slice().reverse().find((transition) => transition.state === 'deferred');
  const decisions = deferredTransition ? [{
    id: deferredTransition.at,
    event_id: event.id,
    action: 'defer',
    reason: deferredTransition.deferOrigin === 'automatic'
      ? 'Automatically snoozed during the focus window configured by the user.'
      : 'User snoozed the notification until a configured break.',
    timestamp: new Date(deferredTransition.at).toISOString(),
  }] : [];
  const latestRemoval = nativeItem?.transitions?.slice().reverse().find((transition) => transition.state === 'removed');
  const removalReason = nativeItem?.removalReason ?? latestRemoval?.reason;
  const outcomeAt = nativeItem?.removedAt ?? latestRemoval?.at ?? nativeItem?.updatedAt ?? Date.now();
  const outcomeType = nativeItem?.state === 'deferred'
    ? 'deferred'
    : removalReason === 1
      ? 'opened_notification'
      : removalReason === 2 || removalReason === 3
        ? 'dismissed'
        : null;
  const observed_outcomes = nativeItem && outcomeType ? [{
    id: outcomeAt,
    event_id: event.id,
    outcome_type: outcomeType,
    interaction_measurements: { removal_reason: removalReason ?? null },
    timestamp: new Date(outcomeAt).toISOString(),
  }] : [];
  return {
    event,
    decisions,
    observed_outcomes,
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

const DEMO_CASES = [
  { app: 'WhatsApp', category: 'direct_message', outcome: 'opened_within_5min', browsing: 9, focus: true },
  { app: 'Instagram', category: 'social_like', outcome: 'dismissed', browsing: 0, focus: true },
  { app: 'Gmail', category: 'email', outcome: 'opened_within_5min', browsing: 6, focus: false },
  { app: 'Slack', category: 'mention', outcome: 'deferred_then_opened', browsing: 4, focus: true },
  { app: 'Calendar', category: 'calendar_reminder', outcome: 'opened_within_5min', browsing: 2, focus: true },
  { app: 'YouTube', category: 'recommendation', outcome: 'ignored', browsing: 0, focus: true },
  { app: 'Teams', category: 'direct_message', outcome: 'deferred_then_opened', browsing: 5, focus: true },
  { app: 'Phone', category: 'call', outcome: 'opened_within_5min', browsing: 3, focus: false },
  { app: 'News', category: 'news', outcome: 'ignored', browsing: 0, focus: true },
  { app: 'WhatsApp', category: 'direct_message', outcome: 'opened_within_5min', browsing: 11, focus: false },
  { app: 'Instagram', category: 'social_like', outcome: 'ignored', browsing: 0, focus: true },
  { app: 'Slack', category: 'build_status', outcome: 'opened_within_5min', browsing: 4, focus: true },
  { app: 'Gmail', category: 'email', outcome: 'dismissed', browsing: 0, focus: true },
  { app: 'Calendar', category: 'calendar_reminder', outcome: 'opened_within_5min', browsing: 2, focus: false },
  { app: 'YouTube', category: 'recommendation', outcome: 'opened_within_5min', browsing: 18, focus: false },
  { app: 'Teams', category: 'mention', outcome: 'deferred_then_opened', browsing: 5, focus: true },
  { app: 'News', category: 'news', outcome: 'dismissed', browsing: 0, focus: false },
  { app: 'Phone', category: 'missed_call', outcome: 'opened_within_5min', browsing: 3, focus: false },
  { app: 'WhatsApp', category: 'direct_message', outcome: 'deferred_then_opened', browsing: 7, focus: true },
  { app: 'Instagram', category: 'social_like', outcome: 'dismissed', browsing: 0, focus: false },
  { app: 'Slack', category: 'mention', outcome: 'opened_within_5min', browsing: 5, focus: false },
  { app: 'Gmail', category: 'email', outcome: 'ignored', browsing: 0, focus: true },
  { app: 'YouTube', category: 'recommendation', outcome: 'ignored', browsing: 0, focus: true },
  { app: 'Calendar', category: 'calendar_reminder', outcome: 'opened_within_5min', browsing: 2, focus: false },
] as const;

export function loadOfflineDemoData(): number {
  const demoEvents: NotificationEventResponse[] = DEMO_CASES.map((item, index) => {
    const timestamp = new Date(Date.now() - (index + 1) * 11 * 60 * 60 * 1000);
    return {
      id: 1_800_000_000_000 + index,
      text: '[Synthetic demo notification; not a real message]',
      source_app: `DEMO · ${item.app}`,
      category: item.category,
      timestamp: timestamp.toISOString(),
      context_data: {
        is_synthetic_demo: true,
        outcome: item.outcome,
        focus_session: item.focus,
        simulated_browsing_minutes: item.browsing,
      },
    };
  });
  writeEvents([...readEvents().filter((event) => event.context_data?.is_synthetic_demo !== true), ...demoEvents]);
  return demoEvents.length;
}

export function clearOfflineDemoData(): void {
  writeEvents(readEvents().filter((event) => event.context_data?.is_synthetic_demo !== true));
}
