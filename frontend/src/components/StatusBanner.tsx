import React from 'react';
import { Layers, CheckCircle2, AlertTriangle } from 'lucide-react';
import { HealthStatus } from '../types';

interface StatusBannerProps {
  health: HealthStatus;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({ health }) => {
  return (
    <div className="system-banner">
      <div className="banner-content">
        <div className="banner-icon">
          <Layers size={24} />
        </div>
        <div>
          <div className="banner-title">Attention Digital Twin &mdash; Counterfactual Analytics Engine</div>
          <div className="banner-desc">
            FastAPI REST backend with SQLite persistence, React 18 TypeScript frontend with Vite proxy,
            and local scikit-learn action-aware counterfactual comparison engine. External LLMs remain optional.
          </div>
        </div>
      </div>

      <div className="banner-stats">
        <div className="stat-chip">
          <div className="stat-label">Vite Proxy API</div>
          <div className="stat-value">
            {health.status === 'healthy' ? (
              <span style={{ color: 'var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={13} /> Connected
              </span>
            ) : health.status === 'loading' ? (
              <span>Connecting...</span>
            ) : (
              <span style={{ color: 'var(--accent-rose)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <AlertTriangle size={13} /> Disconnected
              </span>
            )}
          </div>
        </div>

        <div className="stat-chip">
          <div className="stat-label">Environment</div>
          <div className="stat-value">{health.environment || 'development'}</div>
        </div>

        <div className="stat-chip">
          <div className="stat-label">Service Version</div>
          <div className="stat-value">{health.version || 'v0.1.0'}</div>
        </div>
      </div>
    </div>
  );
};
