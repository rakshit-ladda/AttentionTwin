/**
 * CounterfactualComparison — Phase 6
 * Dedicated Counterfactual Exploration Tab.
 * Provides curated pre-decision scenarios (e.g., Deep Work Slack, Weekend Alert, Late Night Social)
 * plus full custom parameter exploration to compare ALLOW, DEFER, and SUPPRESS outcomes.
 */
import React, { useState, useEffect } from 'react';
import { 
  GitCompare, 
  Sparkles, 
  Clock, 
  Info 
} from 'lucide-react';
import { 
  api, 
  CounterfactualCompareRequest, 
  CounterfactualCompareResponse 
} from '../api';
import { CounterfactualResultPanel } from './CounterfactualResultPanel';

interface PresetScenario {
  id: string;
  name: string;
  description: string;
  request: CounterfactualCompareRequest;
}

const PRESET_SCENARIOS: PresetScenario[] = [
  {
    id: 'deep-work-slack',
    name: 'Direct Message during Deep Work',
    description: 'High-priority team DM arriving in the middle of a focused coding session.',
    request: {
      source_app: 'Slack',
      app_category: 'communication',
      notification_category: 'direct_message',
      text_length: 72,
      hour_of_day: 14,
      day_of_week: 1, // Tuesday
      is_weekend: 0,
      focus_mode: 'deep_work',
      is_focus_session: 1,
      recent_notification_count_15m: 1,
      minutes_since_last_notification: 35.0,
      notification_load_1h: 3,
      app_historical_open_rate: 0.65,
      app_historical_ignore_rate: 0.15,
      user_historical_open_rate: 0.50,
      recent_allow_rate_1h: 0.6,
      recent_suppress_rate_1h: 0.1,
    },
  },
  {
    id: 'meeting-alert',
    name: 'CI/CD Build Alert during Meeting',
    description: 'Automated pipeline notification arriving while in a calendar meeting.',
    request: {
      source_app: 'GitHub',
      app_category: 'work',
      notification_category: 'build_status',
      text_length: 95,
      hour_of_day: 11,
      day_of_week: 2, // Wednesday
      is_weekend: 0,
      focus_mode: 'meetings',
      is_focus_session: 0,
      recent_notification_count_15m: 4,
      minutes_since_last_notification: 6.0,
      notification_load_1h: 9,
      app_historical_open_rate: 0.40,
      app_historical_ignore_rate: 0.45,
      user_historical_open_rate: 0.45,
      recent_allow_rate_1h: 0.4,
      recent_suppress_rate_1h: 0.3,
    },
  },
  {
    id: 'casual-social',
    name: 'Social Mention during Casual Browsing',
    description: 'Social engagement alert arriving during unstructured break or browsing time.',
    request: {
      source_app: 'Instagram',
      app_category: 'social',
      notification_category: 'social_like',
      text_length: 42,
      hour_of_day: 17,
      day_of_week: 4, // Friday
      is_weekend: 0,
      focus_mode: 'casual_browsing',
      is_focus_session: 0,
      recent_notification_count_15m: 0,
      minutes_since_last_notification: 45.0,
      notification_load_1h: 1,
      app_historical_open_rate: 0.30,
      app_historical_ignore_rate: 0.60,
      user_historical_open_rate: 0.55,
      recent_allow_rate_1h: 0.7,
      recent_suppress_rate_1h: 0.1,
    },
  },
  {
    id: 'off-hours-urgent',
    name: 'Infrastructure Incident Off-Hours',
    description: 'Critical system spike alerting late on a weekend evening.',
    request: {
      source_app: 'Datadog',
      app_category: 'system',
      notification_category: 'cpu_spike',
      text_length: 120,
      hour_of_day: 22,
      day_of_week: 6, // Sunday
      is_weekend: 1,
      focus_mode: 'off_hours',
      is_focus_session: 0,
      recent_notification_count_15m: 0,
      minutes_since_last_notification: 180.0,
      notification_load_1h: 0,
      app_historical_open_rate: 0.75,
      app_historical_ignore_rate: 0.10,
      user_historical_open_rate: 0.40,
      recent_allow_rate_1h: 0.2,
      recent_suppress_rate_1h: 0.5,
    },
  },
];

export const CounterfactualComparison: React.FC = () => {
  const [activePresetId, setActivePresetId] = useState<string>(PRESET_SCENARIOS[0].id);
  const [result, setResult] = useState<CounterfactualCompareResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runComparison = async (params: CounterfactualCompareRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.compareCounterfactuals(params);
      setResult(response);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Counterfactual evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Automatically evaluate the initial preset
    runComparison(PRESET_SCENARIOS[0].request);
  }, []);

  const selectPreset = (preset: PresetScenario) => {
    setActivePresetId(preset.id);
    runComparison(preset.request);
  };

  return (
    <div className="live-section">
      <div className="section-header-bar">
        <div className="section-title-wrap">
          <div className="section-icon-large">
            <GitCompare size={22} />
          </div>
          <div>
            <h2 className="section-title">Counterfactual Comparison Engine</h2>
            <p className="section-tagline">
              Invariant Context Evaluation: Compare outcomes across ALLOW, DEFER, and SUPPRESS for identical context
            </p>
          </div>
        </div>
      </div>

      {/* Preset Scenario Selector */}
      <div className="preset-selector-container">
        <div className="preset-header-label">
          <Sparkles size={16} className="indigo" />
          <span>Curated Scenarios (Holding pre-decision arrival features invariant)</span>
        </div>
        <div className="preset-grid">
          {PRESET_SCENARIOS.map((preset) => {
            const isSelected = activePresetId === preset.id;
            return (
              <button
                key={preset.id}
                className={`preset-card-btn ${isSelected ? 'active' : ''}`}
                onClick={() => selectPreset(preset)}
              >
                <div className="preset-name">{preset.name}</div>
                <div className="preset-desc">{preset.description}</div>
                <div className="preset-tags">
                  <span className="preset-tag">{preset.request.source_app}</span>
                  <span className="preset-tag">{preset.request.focus_mode}</span>
                  <span className="preset-tag">{preset.request.hour_of_day}:00</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="alert-error" style={{ marginBottom: '1.5rem' }}>
          <Info size={16} /> {error}
        </div>
      )}

      {loading && !result && (
        <div className="empty-state">
          <Clock size={36} className="spin" style={{ color: 'var(--accent-cyan)', marginBottom: '0.75rem' }} />
          <p>Running counterfactual inference across candidate actions...</p>
        </div>
      )}

      {result && (
        <div className="cf-results-wrapper">
          <CounterfactualResultPanel result={result} />
        </div>
      )}
    </div>
  );
};
