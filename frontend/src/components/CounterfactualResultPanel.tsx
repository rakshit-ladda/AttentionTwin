/**
 * CounterfactualResultPanel — Phase 6
 * Displays counterfactual comparison results with Recharts bar chart.
 * Always shows disclaimers. Never fabricates values beyond the API response.
 */
import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { AlertTriangle, Info } from 'lucide-react';
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

  const best = result.scenarios.reduce((a, b) =>
    b.probability_opened_quickly > a.probability_opened_quickly ? b : a
  );

  return (
    <div className="cf-result-panel">
      {/* Header */}
      <div className="cf-result-header">
        <span className="cf-result-title">Counterfactual Comparison</span>
        <span className="model-badge">model: {result.model_version}</span>
      </div>

      {/* Chart */}
      <div className="cf-chart-wrap">
        <div className="chart-label">P(opened quickly) by action</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="action"
              tickFormatter={(v: string) => v.toUpperCase()}
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={45}
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
        {result.scenarios.map((s: CounterfactualScenarioResult) => (
          <div
            key={s.proposed_action}
            className={`cf-scenario-card ${s.proposed_action === best.proposed_action ? 'cf-best' : ''}`}
            style={{ borderTopColor: ACTION_COLORS[s.proposed_action] }}
          >
            <div className="cf-scenario-action-row">
              <span
                className="cf-action-chip"
                style={{ background: `${ACTION_COLORS[s.proposed_action]}22`, color: ACTION_COLORS[s.proposed_action] }}
              >
                {s.proposed_action.toUpperCase()}
              </span>
              {s.proposed_action === best.proposed_action && (
                <span className="cf-best-badge">highest engagement</span>
              )}
              <span className="cf-risk-badge" style={riskBadgeStyle(s.expected_interruption_risk)}>
                {s.expected_interruption_risk} risk
              </span>
            </div>

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

            <p className="cf-timing-text">{s.timing_explanation}</p>

            {s.support_warning && (
              <div className="cf-warning">
                <AlertTriangle size={12} /> {s.support_warning}
              </div>
            )}
          </div>
        ))}
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
