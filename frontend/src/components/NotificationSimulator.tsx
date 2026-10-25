/**
 * NotificationSimulator — Phase 6
 * Lets the user describe an incoming notification, submits it to the backend
 * (POST /api/events), and immediately fires a counterfactual comparison.
 *
 * Constraints preserved:
 * - Does NOT fabricate predictions.
 * - Every result includes the backend disclaimer.
 * - No synthetic data is written to attention_twin.db by this component.
 *   The user chooses whether to record via "Save Event".
 */
import React, { useState } from 'react';
import {
  BellRing, Send, AlertTriangle, CheckCircle2, Clock
} from 'lucide-react';
import {
  api,
  CounterfactualCompareRequest,
  CounterfactualCompareResponse,
} from '../api';
import { CounterfactualResultPanel } from './CounterfactualResultPanel';

const FOCUS_MODES = [
  'deep_work',
  'meetings',
  'casual_browsing',
  'off_hours',
  'break',
];

const APP_CATEGORIES = [
  'communication',
  'work',
  'social',
  'system',
  'productivity',
  'entertainment',
  'finance',
  'health',
];

const NOTIF_CATEGORIES = [
  'direct_message',
  'mention',
  'email',
  'calendar_reminder',
  'alert',
  'cpu_spike',
  'build_status',
  'news',
  'social_like',
];

interface FormState {
  source_app: string;
  app_category: string;
  notification_category: string;
  text: string;
  focus_mode: string;
  is_focus_session: number;
  hour_of_day: number;
  day_of_week: number;
}

const now = new Date();
const defaultForm: FormState = {
  source_app: 'Slack',
  app_category: 'communication',
  notification_category: 'direct_message',
  text: 'Hey, are you free for a quick sync?',
  focus_mode: 'deep_work',
  is_focus_session: 1,
  hour_of_day: now.getHours(),
  day_of_week: now.getDay() === 0 ? 6 : now.getDay() - 1, // 0=Mon
};

export const NotificationSimulator: React.FC = () => {
  const [form, setForm] = useState<FormState>(defaultForm);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CounterfactualCompareResponse | null>(null);
  const [savedEventId, setSavedEventId] = useState<number | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const isWeekend = form.day_of_week >= 5 ? 1 : 0;

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    // Clear previous result when inputs change
    setResult(null);
    setSavedEventId(null);
    setSaveSuccess(false);
  }

  const buildRequest = (): CounterfactualCompareRequest => ({
    source_app: form.source_app.trim() || 'Unknown',
    app_category: form.app_category,
    notification_category: form.notification_category,
    text_length: Math.max(1, form.text.length),
    hour_of_day: form.hour_of_day,
    day_of_week: form.day_of_week,
    is_weekend: isWeekend,
    focus_mode: form.focus_mode,
    is_focus_session: form.is_focus_session,
    recent_notification_count_15m: 2,
    minutes_since_last_notification: 18,
    notification_load_1h: 5,
    app_historical_open_rate: 0.55,
    app_historical_ignore_rate: 0.25,
    user_historical_open_rate: 0.5,
    recent_allow_rate_1h: 0.5,
    recent_suppress_rate_1h: 0.2,
  });

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaveSuccess(false);
    try {
      const res = await api.compareCounterfactuals(buildRequest());
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEvent = async () => {
    if (saveLoading || savedEventId != null) return;
    setSaveLoading(true);
    setError(null);
    try {
      const evt = await api.createEvent({
        text: form.text,
        source_app: form.source_app,
        category: form.notification_category,
        context_data: {
          focus_mode: form.focus_mode,
          is_focus_session: form.is_focus_session,
          hour_of_day: form.hour_of_day,
          day_of_week: form.day_of_week,
        },
      });
      setSavedEventId(evt.id);
      setSaveSuccess(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaveLoading(false);
    }
  };

  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="live-section">
      <div className="section-header-bar">
        <div className="section-title-wrap">
          <div className="section-icon-large"><BellRing size={22} /></div>
          <div>
            <h2 className="section-title">Notification Simulator</h2>
            <p className="section-tagline">
              Describe an incoming notification to compare ALLOW / DEFER / SUPPRESS outcomes
            </p>
          </div>
        </div>
      </div>

      <div className="sim-layout">
        {/* Form panel */}
        <div className="sim-form-card">
          <div className="form-section-label">Notification Details</div>

          <label className="field-label">App Name</label>
          <input
            className="field-input"
            value={form.source_app}
            onChange={e => set('source_app', e.target.value)}
            placeholder="e.g. Slack, Gmail, GitHub"
          />

          <div className="field-row">
            <div className="field-col">
              <label className="field-label">App Category</label>
              <select className="field-select" value={form.app_category}
                onChange={e => set('app_category', e.target.value)}>
                {APP_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="field-col">
              <label className="field-label">Notification Type</label>
              <select className="field-select" value={form.notification_category}
                onChange={e => set('notification_category', e.target.value)}>
                {NOTIF_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <label className="field-label">Notification Text</label>
          <textarea
            className="field-textarea"
            rows={3}
            value={form.text}
            onChange={e => set('text', e.target.value)}
            placeholder="Notification content (used only for text_length feature)"
          />
          <div className="char-count">{form.text.length} chars</div>

          <div className="form-section-label" style={{ marginTop: '1rem' }}>Context</div>

          <div className="field-row">
            <div className="field-col">
              <label className="field-label">Focus Mode</label>
              <select className="field-select" value={form.focus_mode}
                onChange={e => set('focus_mode', e.target.value)}>
                {FOCUS_MODES.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="field-col">
              <label className="field-label">Focus Session Active</label>
              <select className="field-select" value={form.is_focus_session}
                onChange={e => set('is_focus_session', Number(e.target.value))}>
                <option value={1}>Yes</option>
                <option value={0}>No</option>
              </select>
            </div>
          </div>

          <div className="field-row">
            <div className="field-col">
              <label className="field-label">Hour of Day ({form.hour_of_day}:00)</label>
              <input type="range" min={0} max={23} value={form.hour_of_day}
                className="field-range"
                onChange={e => set('hour_of_day', Number(e.target.value))} />
            </div>
            <div className="field-col">
              <label className="field-label">Day of Week</label>
              <select className="field-select" value={form.day_of_week}
                onChange={e => set('day_of_week', Number(e.target.value))}>
                {dayLabels.map((d, i) => <option key={i} value={i}>{d}</option>)}
              </select>
            </div>
          </div>

          <div className="sim-actions">
            <button
              className="btn-primary"
              onClick={handleCompare}
              disabled={loading}
            >
              {loading ? (
                <><Clock size={16} className="spin" /> Comparing…</>
              ) : (
                <><Send size={16} /> Compare Actions</>
              )}
            </button>

            {result && !saveSuccess && (
              <button
                className="btn-secondary"
                onClick={handleSaveEvent}
                disabled={saveLoading}
              >
                {saveLoading ? 'Saving…' : 'Save Event to DB'}
              </button>
            )}

            {saveSuccess && savedEventId != null && (
              <span className="save-success-badge">
                <CheckCircle2 size={14} /> Saved as Event #{savedEventId}
              </span>
            )}
          </div>

          {error && (
            <div className="alert-error" style={{ marginTop: '0.75rem' }}>
              <AlertTriangle size={14} /> {error}
            </div>
          )}
        </div>

        {/* Result panel */}
        <div className="sim-result-area">
          {!result && !loading && (
            <div className="empty-state">
              <GitCompareIcon />
              <p>Fill in the notification details and click <strong>Compare Actions</strong> to see counterfactual predictions.</p>
            </div>
          )}
          {result && <CounterfactualResultPanel result={result} />}
        </div>
      </div>
    </div>
  );
};

// Inline icon to avoid import cycle
const GitCompareIcon: React.FC = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
    style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
    <circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/>
    <path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M11 18H8a2 2 0 0 1-2-2V9"/>
    <path d="m9 3-3 3 3 3"/><path d="m15 21 3-3-3-3"/>
  </svg>
);
