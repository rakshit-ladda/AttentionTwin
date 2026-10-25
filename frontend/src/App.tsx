import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { StatusBanner } from './components/StatusBanner';
import { AttentionProfile } from './components/AttentionProfile';
import { NotificationSimulator } from './components/NotificationSimulator';
import { CounterfactualComparison } from './components/CounterfactualComparison';
import { HistoryPanel } from './components/HistoryPanel';
import { NotificationAccessPanel } from './components/NotificationAccessPanel';
import { NavTab, HealthStatus } from './types';
import { api, getApiBaseUrl, isNativeApp } from './api';
import './App.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('counterfactual');
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus>(() => {
    const baseUrl = getApiBaseUrl();
    const isNative = isNativeApp();
    if (isNative && !baseUrl) {
      return {
        status: 'not_configured',
        errorMessage: 'Backend URL not configured on mobile.',
        baseUrl: '',
      };
    }
    return {
      status: 'checking',
      baseUrl,
    };
  });

  const checkHealth = useCallback(async () => {
    const baseUrl = getApiBaseUrl();
    const isNative = isNativeApp();

    if (isNative && !baseUrl) {
      setHealth({
        status: 'not_configured',
        errorMessage: 'Backend URL not configured. Tap Settings (⚙) to enter your laptop Wi-Fi address.',
        baseUrl: '',
      });
      return;
    }

    setHealth((prev) => ({ ...prev, status: 'checking', baseUrl }));
    const startTime = performance.now();
    try {
      const data = await api.health();
      const endTime = performance.now();
      const latencyMs = Math.round(endTime - startTime);

      setHealth({
        status: data.status === 'healthy' ? 'connected' : 'offline',
        service: data.service,
        version: data.version,
        environment: data.environment,
        timestamp: data.timestamp,
        latencyMs,
        baseUrl,
      });
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown connection error';
      setHealth({
        status: 'offline',
        errorMessage: errorMsg,
        baseUrl,
      });
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return (
    <div className="app-container">
      <Header
        health={health}
        onRefreshHealth={checkHealth}
        isSettingsOpen={isSettingsOpen}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onCloseSettings={() => setIsSettingsOpen(false)}
      />
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="app-main">
        {isNativeApp() && <NotificationAccessPanel />}
        <StatusBanner
          health={health}
          onRetry={checkHealth}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />
        {activeTab === 'profile' && <AttentionProfile />}
        {activeTab === 'simulator' && <NotificationSimulator />}
        {activeTab === 'counterfactual' && <CounterfactualComparison />}
        {activeTab === 'history' && <HistoryPanel />}
      </main>

      <footer className="app-footer">
        <div>
          <strong>AttentionTwin</strong> &mdash; CASCADE 2026 Hackathon (IIIT Nagpur)
        </div>
        <div className="footer-links">
          <span>Backend API: <code>/api/health</code></span>
          <span>Local SQLite &amp; scikit-learn Engine</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
