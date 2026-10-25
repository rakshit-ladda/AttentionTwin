/**
 * CounterfactualResultPanel — Phase 6 & Phase 8
 * Displays counterfactual comparison results across ALLOW, DEFER, and SUPPRESS.
 * Estimates interruption duration, app opening probability, browsing time, and task-resumption delay.
 * Recommends optimal action based on cognitive attention preservation policy.
 */
import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { AlertTriangle, Info, Check, Sparkles } from 'lucide-react';
import { CounterfactualCompareResponse, CounterfactualScenarioResult } from '../api';

interface Props {
  result: CounterfactualCompareResponse;
}

const ACTION_COLORS: Record<string, string> = {
  allow: '#06b6d4',
  defer: '#f59e0b',
  suppress: '#6366f1',
};

const RISK_COLORS: Record<string, string> = {
  high: '#f87171',
  medium: '#fbbf24',
  low: '#34d399',
  negligible: '#94a3b8',
};

function riskBadgeStyle(risk: string) {
  return {
    background: `${RISK_COLORS[risk] ?? '#94a3b8'}22`,
    color: RISK_COLORS[risk] ?? '#94a3b8',
    border: `1px solid ${RISK_COLORS[risk] ?? '#94a3b8'}55`,
  };
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: { value: number; name: string }[];
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-color)',
      borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.8rem',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label?.toUpperCase()}</div>
      <div style={{ color: 'var(--text-secondary)' }}>
        P(opened quickly): <strong style={{ color: '#38bdf8' }}>
          {(payload[0].value * 100).toFixed(1)}%
        </strong>
      </div>
    </div>
  );
};

export const CounterfactualResultPanel: React.FC<Props> = ({ result }) => {
  const chartData = result.scenarios.map((s) => ({
    action: s.proposed_action,
    probability: s.probability_opened_quickly,
    label: s.predicted_label,
    risk: s.expected_interruption_risk,
  }));

  return (
    <div className="cf-result-panel">
      {/* Header */}
      <div className="cf-result-header">
        <span className="cf-result-title">Counterfactual Comparison</span>
        <span className="model-badge">model: {result.model_version}</span>
      </div>

      {/* Recommended Action Policy Banner */}
      {result.recommended_action && (
        <div className="rec-policy-banner">
          <div className="rec-policy-header">
            <Sparkles size={16} className="indigo" />
            <span>
              Recommended Policy: <strong style={{ color: ACTION_COLORS[result.recommended_action] }}>
                {result.recommended_action.toUpperCase()}
              </strong>
            </span>
          </div>
          <p className="rec-policy-text">{result.recommendation_rationale}</p>
        </div>
      )}

      {/* Chart */}
      <div className="cf-chart-wrap">
        <div className="chart-label">P(opened quickly) by action</div>
        <ResponsiveContainer width="100%" height={210}>
          <BarChart data={chartData} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="action"
              tickFormatter={(v: string) => v.toUpperCase()}
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={38}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0.5} stroke="#334155" strokeDasharray="4 4" />
            <Bar dataKey="probability" radius={[6, 6, 0, 0]} maxBarSize={80}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={ACTION_COLORS[entry.action] ?? '#64748b'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario cards */}
      <div className="cf-scenario-grid">
        {result.scenarios.map((s: CounterfactualScenarioResult) => {
          const isRec = s.is_recommended || s.proposed_action === result.recommended_action;
          return (
            <div
              key={s.proposed_action}
              className={`cf-scenario-card ${isRec ? 'cf-recommended' : ''}`}
              style={{ borderTopColor: ACTION_COLORS[s.proposed_action] }}
            >
              <div className="cf-scenario-action-row">
                <span
                  className="cf-action-chip"
                  style={{ background: `${ACTION_COLORS[s.proposed_action]}22`, color: ACTION_COLORS[s.proposed_action] }}
                >
                  {s.proposed_action.toUpperCase()}
                </span>
                {isRec && (
                  <span className="cf-recommended-badge">
                    <Check size={11} /> RECOMMENDED
                  </span>
                )}
                <span className="cf-risk-badge" style={riskBadgeStyle(s.expected_interruption_risk)}>
                  {s.expected_interruption_risk} risk
                </span>
              </div>

              {/* Main Probability */}
              <div className="cf-prob-row">
                <span className="cf-prob-val">
                  {(s.probability_opened_quickly * 100).toFixed(1)}%
                </span>
                <span className="cf-prob-label">P(opened quickly)</span>
              </div>

              <div className="cf-prob-bar-bg">
                <div
                  className="cf-prob-bar-fill"
                  style={{
                    width: `${(s.probability_opened_quickly * 100).toFixed(1)}%`,
                    background: ACTION_COLORS[s.proposed_action],
                  }}
                />
              </div>

              {/* Cognitive & Task Disruption Metrics */}
              <div className="cf-metrics-table">
                <div className="cf-metric-row total-loss">
                  <span className="cf-metric-name">Interruption Duration:</span>
                  <span className="cf-metric-val mono">
                    {s.estimated_interruption_minutes.toFixed(1)} min
                  </span>
                </div>
                <div className="cf-metric-row">
                  <span className="cf-metric-name">Time Spent Browsing:</span>
                  <span className="cf-metric-val mono">
                    {s.estimated_browsing_minutes.toFixed(1)} min
                  </span>
                </div>
                <div className="cf-metric-row">
                  <span className="cf-metric-name">Task-Resumption Delay:</span>
                  <span className="cf-metric-val mono">
                    {s.estimated_resumption_delay_minutes.toFixed(1)} min
                  </span>
                </div>
                <div className="cf-metric-row">
                  <span className="cf-metric-name">Delivery Schedule:</span>
                  <span className="cf-metric-val mono">
                    {s.deferred_delivery_minutes
                      ? `+${s.deferred_delivery_minutes}m (Break)`
                      : s.proposed_action === 'suppress'
                      ? 'Silent Digest'
                      : 'Immediate'}
                  </span>
                </div>
              </div>

              <p className="cf-timing-text">{s.timing_explanation}</p>

              {s.support_warning && (
                <div className="cf-warning">
                  <AlertTriangle size={12} /> {s.support_warning}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Narrative summary */}
      <div className="cf-summary-box">
        <div className="cf-summary-title">Comparative Analysis</div>
        <p className="cf-summary-text">{result.relative_comparison_summary}</p>
      </div>

      {/* Disclaimers */}
      <div className="cf-disclaimer">
        <Info size={14} />
        <div>
          <strong>Provenance:</strong> {result.data_provenance}<br />
          <strong>Limitations:</strong> {result.limitations_disclaimer}
        </div>
      </div>
    </div>
  );
};
