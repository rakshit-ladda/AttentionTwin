import React from 'react';
import { RefreshCw, Cpu } from 'lucide-react';
import { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus;
  onRefreshHealth: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onRefreshHealth }) => {
  const getStatusText = () => {
    switch (health.status) {
      case 'healthy':
        return `Backend Online (${health.latencyMs ?? 0}ms)`;
      case 'loading':
        return 'Connecting to API...';
      case 'error':
      case 'unhealthy':
        return 'Backend Offline';
      default:
        return 'Status Unknown';
    }
  };

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">
          <Cpu size={24} />
        </div>
        <div>
          <div className="brand-title">AttentionTwin</div>
          <div className="brand-subtitle">
            Personal Attention Digital Twin
            <span className="event-badge">CASCADE 2026</span>
          </div>
        </div>
      </div>

      <div className="header-meta">
        <div className="health-badge" title={health.errorMessage || `Endpoint: /api/health`}>
          <span className={`pulse-dot ${health.status}`} />
          <span>{getStatusText()}</span>
          <button 
            className="refresh-btn" 
            onClick={onRefreshHealth}
            title="Refresh backend health status"
            aria-label="Refresh backend health"
          >
            <RefreshCw size={13} className={health.status === 'loading' ? 'spin' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
};
