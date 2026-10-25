import React from 'react';
import { Layers, CheckCircle2, AlertTriangle, RefreshCw, Settings, WifiOff } from 'lucide-react';
import { HealthStatus } from '../types';
import { isNativeApp } from '../api';

interface StatusBannerProps {
  health: HealthStatus;
  onRetry?: () => void;
  onOpenSettings?: () => void;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  health,
  onRetry,
  onOpenSettings,
}) => {
  const isNative = isNativeApp();

  const renderStatusValue = () => {
    switch (health.status) {
      case 'connected':
        return (
          <span style={{ color: 'var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={13} /> Connected
          </span>
        );
      case 'local':
        return (
          <span style={{ color: 'var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={13} /> On-device
          </span>
        );
      case 'checking':
        return (
          <span style={{ color: 'var(--accent-amber)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <RefreshCw size={13} className="spin" /> Checking...
          </span>
        );
      case 'not_configured':
        return (
          <span
            style={{ color: '#a5b4fc', display: 'inline-flex', alignItems: 'center', gap: '4px', cursor: onOpenSettings ? 'pointer' : undefined }}
            onClick={onOpenSettings}
          >
            <Settings size={13} /> Not Configured
          </span>
        );
      case 'offline':
      default:
        return (
          <span style={{ color: 'var(--accent-rose)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={13} /> Disconnected
          </span>
        );
    }
  };

  return (
    <div className="system-banner">
      <div className="banner-content">
        <div className="banner-icon">
          <Layers size={24} />
        </div>
        <div className="banner-text-block">
          <div className="banner-title">AttentionTwin &mdash; {health.status === 'local' ? 'On-device runtime' : 'Counterfactual Analytics Engine'}</div>
          <div className="banner-desc">
            {health.status === 'local'
              ? 'Runs without the laptop backend. Offline guidance uses conservative rules, not a trained personal model; notification decisions require your confirmation.'
              : 'FastAPI REST backend with SQLite persistence, React 18 TypeScript frontend, and a scikit-learn comparison engine.'}
          </div>
        </div>
      </div>

      {health.status === 'not_configured' && (
        <div className="banner-notice banner-notice-warning">
          <div className="banner-notice-text">
            <WifiOff size={15} className="banner-notice-icon" />
            <span>
              <strong>Android Mobile Setup:</strong> Backend URL is not configured.
              Connect your phone to your laptop hotspot/Wi-Fi and configure the backend address.
            </span>
          </div>
          {onOpenSettings && (
            <button className="btn-banner-action" onClick={onOpenSettings}>
              <Settings size={13} /> Configure Backend
            </button>
          )}
        </div>
      )}

      {health.status === 'offline' && (
        <div className="banner-notice banner-notice-error">
          <div className="banner-notice-text">
            <AlertTriangle size={15} className="banner-notice-icon" />
            <span>
              Cannot reach backend{health.baseUrl ? ` at ${health.baseUrl}` : ''}.
              Ensure FastAPI is running on host <code>0.0.0.0</code> and port 8000.
            </span>
          </div>
          <div className="banner-notice-actions">
            {onRetry && (
              <button className="btn-banner-action" onClick={onRetry}>
                <RefreshCw size={13} /> Retry
              </button>
            )}
            {onOpenSettings && (
              <button className="btn-banner-action secondary" onClick={onOpenSettings}>
                <Settings size={13} /> Change URL
              </button>
            )}
          </div>
        </div>
      )}

      <div className="banner-stats">
        <div className="stat-chip">
          <div className="stat-label">{health.status === 'local' ? 'Runtime' : isNative ? 'Backend Link' : 'API Connection'}</div>
          <div className="stat-value">{renderStatusValue()}</div>
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
