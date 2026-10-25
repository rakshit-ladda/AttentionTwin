import React, { useState } from 'react';
import { RefreshCw, Cpu, Settings, X, Wifi, Smartphone, Check } from 'lucide-react';
import { HealthStatus } from '../types';
import { getApiBaseUrl, setApiBaseUrl } from '../api';

interface HeaderProps {
  health: HealthStatus;
  onRefreshHealth: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onRefreshHealth }) => {
  const [showSettings, setShowSettings] = useState(false);
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [savedSuccess, setSavedSuccess] = useState(false);

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

  const handleSaveUrl = () => {
    setApiBaseUrl(apiUrl);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
    onRefreshHealth();
  };

  const setPresetUrl = (preset: string) => {
    setApiUrl(preset);
  };

  return (
    <>
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
          <div className="health-badge" title={health.errorMessage || `Endpoint: ${apiUrl || ''}/api/health`}>
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

          <button
            className="icon-btn header-settings-btn"
            onClick={() => setShowSettings(true)}
            title="Configure Backend Connection"
            aria-label="Configure Backend Connection"
          >
            <Settings size={16} />
          </button>
        </div>
      </header>

      {/* Backend Connection Modal */}
      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-wrap">
                <Wifi size={18} className="indigo" />
                <span>Backend Connection Settings</span>
              </div>
              <button className="icon-btn" onClick={() => setShowSettings(false)}>
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              <p className="modal-desc">
                When running as a mobile Android APK, specify your laptop host or server IP address.
                Leave blank to use the default Vite development proxy (<code>/api</code>).
              </p>

              <label className="field-label">API Base URL</label>
              <input
                className="field-input mono"
                type="text"
                placeholder="e.g. http://192.168.1.15:8000"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
              />

              <div className="quick-presets">
                <span className="preset-label">Quick Presets:</span>
                <button
                  type="button"
                  className="preset-chip"
                  onClick={() => setPresetUrl('')}
                >
                  Local Proxy (Blank)
                </button>
                <button
                  type="button"
                  className="preset-chip"
                  onClick={() => setPresetUrl('http://10.0.2.2:8000')}
                >
                  <Smartphone size={12} /> Android Emulator (10.0.2.2:8000)
                </button>
              </div>

              <div className="connection-info-box">
                <strong>Wi-Fi Setup for Physical Android Phones:</strong>
                <ol>
                  <li>Connect your phone and laptop to the same Wi-Fi network.</li>
                  <li>Find your laptop&apos;s IP (e.g., run <code>ipconfig</code>).</li>
                  <li>Start the FastAPI backend with: <code>--host 0.0.0.0 --port 8000</code>.</li>
                  <li>Enter <code>http://&lt;LAPTOP-IP&gt;:8000</code> above and save.</li>
                </ol>
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => setShowSettings(false)}
              >
                Close
              </button>
              <button
                className="btn-primary"
                onClick={handleSaveUrl}
              >
                {savedSuccess ? (
                  <><Check size={14} /> Saved!</>
                ) : (
                  'Save & Test Connection'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
