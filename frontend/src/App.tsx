import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { StatusBanner } from './components/StatusBanner';
import { PlaceholderSection } from './components/PlaceholderSection';
import { NavTab, HealthStatus } from './types';
import './App.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('counterfactual');
  const [health, setHealth] = useState<HealthStatus>({
    status: 'loading',
  });

  const checkHealth = useCallback(async () => {
    setHealth((prev) => ({ ...prev, status: 'loading' }));
    const startTime = performance.now();
    try {
      const response = await fetch('/api/health');
      const endTime = performance.now();
      const latencyMs = Math.round(endTime - startTime);

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      setHealth({
        status: data.status === 'healthy' ? 'healthy' : 'unhealthy',
        service: data.service,
        version: data.version,
        environment: data.environment,
        timestamp: data.timestamp,
        latencyMs,
      });
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown connection error';
      setHealth({
        status: 'error',
        errorMessage: errorMsg,
      });
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return (
    <div className="app-container">
      <Header health={health} onRefreshHealth={checkHealth} />
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="app-main">
        <StatusBanner health={health} />
        <PlaceholderSection tab={activeTab} />
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
