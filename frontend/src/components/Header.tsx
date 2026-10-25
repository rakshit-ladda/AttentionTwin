import React, { useState, useEffect } from 'react';
import { RefreshCw, Cpu, Settings, X, Wifi, Smartphone, Check, AlertCircle } from 'lucide-react';
import { HealthStatus } from '../types';
import { getApiBaseUrl, setApiBaseUrl, normalizeApiBaseUrl, isNativeApp } from '../api';

interface HeaderProps {
  health: HealthStatus;
  onRefreshHealth: () => void;
  isSettingsOpen?: boolean;
  onOpenSettings?: () => void;
  onCloseSettings?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  onRefreshHealth,
  isSettingsOpen: controlledIsOpen,
  onOpenSettings,
  onCloseSettings,
}) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const showSettings = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const setShowSettings = (open: boolean) => {
    if (open) {
      if (onOpenSettings) onOpenSettings();
      else setInternalIsOpen(true);
    } else {
      if (onCloseSettings) onCloseSettings();
      else setInternalIsOpen(false);
    }
  };

  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [savedSuccess, setSavedSuccess] = useState(false);
  const isNative = isNativeApp();

  // Sync internal state if storage changes
  useEffect(() => {
    if (showSettings) {
      setApiUrl(getApiBaseUrl());
    }
  }, [showSettings]);

  const getStatusText = () => {
    switch (health.status) {
      case 'connected':
        return `Online (${health.latencyMs ?? 0}ms)`;
      case 'checking':
        return 'Checking...';
      case 'not_configured':
        return 'Not Configured';
      case 'offline':
        return 'Offline';
      default:
        return 'Status Unknown';
    }
  };

  const getPulseDotClass = () => {
    switch (health.status) {
      case 'connected':
        return 'pulse-dot connected';
      case 'checking':
        return 'pulse-dot checking';
      case 'not_configured':
        return 'pulse-dot not-configured';
      case 'offline':
      default:
        return 'pulse-dot offline';
    }
  };

  const handleSaveUrl = () => {
    const normalized = normalizeApiBaseUrl(apiUrl);
    setApiUrl(normalized);
    setApiBaseUrl(normalized);
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
            <Cpu size={22} />
          </div>
          <div className="brand-text">
            <div className="brand-title">AttentionTwin</div>
            <div className="brand-subtitle">
              <span>Personal Attention Digital Twin</span>
              <span className="event-badge">CASCADE 2026</span>
            </div>
          </div>
        </div>

        <div className="header-meta">
          <div
            className={`health-badge status-${health.status}`}
            title={
              health.errorMessage ||
              (health.status === 'not_configured'
                ? 'Backend URL not configured. Tap Settings (⚙) to enter your laptop Wi-Fi address.'
                : `Endpoint: ${health.baseUrl || 'local Vite proxy'}/api/health`)
            }
            onClick={() => health.status === 'not_configured' && setShowSettings(true)}
            style={health.status === 'not_configured' ? { cursor: 'pointer' } : undefined}
          >
            <span className={getPulseDotClass()} />
            <span className="health-status-text">{getStatusText()}</span>
            <button
              className="refresh-btn"
              onClick={(e) => {
                e.stopPropagation();
                onRefreshHealth();
              }}
              title="Refresh backend health status"
              aria-label="Refresh backend health"
            >
              <RefreshCw size={13} className={health.status === 'checking' ? 'spin' : ''} />
            </button>
          </div>

          <button
            className={`icon-btn header-settings-btn ${health.status === 'not_configured' ? 'highlight-pulse' : ''}`}
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
                {isNative ? (
                  <>
                    When running on an Android device, enter your laptop&apos;s Wi-Fi / hotspot IP address
                    and port (e.g. <code>http://10.33.129.111:8000</code>).
                  </>
                ) : (
                  <>
                    When running in local web development, leave blank to use the Vite proxy (
                    <code>/api</code>), or specify an explicit backend URL.
                  </>
                )}
              </p>

              <div className="current-url-indicator">
                <span className="current-url-label">Active Base URL:</span>
                <span className="current-url-val mono">
                  {getApiBaseUrl() || (isNative ? '⚠️ Not configured' : 'http://localhost:5173/api (Vite proxy)')}
                </span>
              </div>

              <label className="field-label" htmlFor="backend-url-input">
                API Base URL (Protocol + IP/Host + Port)
              </label>
              <input
                id="backend-url-input"
                className="field-input mono"
                type="text"
                placeholder="e.g. http://10.33.129.111:8000"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
              />

              <div className="quick-presets">
                <span className="preset-label">Quick Presets:</span>
                <button
                  type="button"
                  className="preset-chip"
                  onClick={() => setPresetUrl('http://10.33.129.111:8000')}
                >
                  <Wifi size={12} /> Hotspot (10.33.129.111:8000)
                </button>
                <button
                  type="button"
                  className="preset-chip"
                  onClick={() => setPresetUrl('http://10.0.2.2:8000')}
                >
                  <Smartphone size={12} /> Emulator (10.0.2.2:8000)
                </button>
                <button
                  type="button"
                  className="preset-chip"
                  onClick={() => setPresetUrl('')}
                >
                  Reset / Blank (Web Proxy)
                </button>
              </div>

              {health.status === 'offline' && health.errorMessage && (
                <div className="connection-error-box">
                  <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 2 }} />
                  <div>{health.errorMessage}</div>
                </div>
              )}

              <div className="connection-info-box">
                <strong>Wi-Fi Setup for Physical Android Phones:</strong>
                <ol>
                  <li>Connect phone and laptop to the same Wi-Fi / hotspot.</li>
                  <li>Find your laptop&apos;s IP address (run <code>ipconfig</code>).</li>
                  <li>
                    Start FastAPI backend on laptop with:
                    <br />
                    <code>python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000</code>
                  </li>
                  <li>Enter <code>http://&lt;LAPTOP-IP&gt;:8000</code> above and tap Save.</li>
                </ol>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowSettings(false)}>
                Close
              </button>
              <button className="btn-primary" onClick={handleSaveUrl}>
                {savedSuccess ? (
                  <>
                    <Check size={14} /> Saved &amp; Testing...
                  </>
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
