/**
 * AttentionProfile — Phase 6
 * Live system information: model status, event counts, and feature info.
 * No fabricated metrics. All values come directly from /api/models/status and /api/events.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { UserCheck, RefreshCw, Brain, Database, Cpu, AlertTriangle } from 'lucide-react';
import { api, ModelStatusResponse, NotificationEventResponse } from '../api';

export const AttentionProfile: React.FC = () => {
  const [modelStatus, setModelStatus] = useState<ModelStatusResponse | null>(null);
  const [events, setEvents] = useState<NotificationEventResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isOfflineRules = modelStatus?.model_version?.startsWith('offline-rules') ?? false;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [status, evts] = await Promise.all([api.modelStatus(), api.listEvents(500)]);
      setModelStatus(status);
      setEvents(evts);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="live-section">
      <div className="section-header-bar">
        <div className="section-title-wrap">
          <div className="section-icon-large"><UserCheck size={22} /></div>
          <div>
            <h2 className="section-title">Attention Profile</h2>
            <p className="section-tagline">Live model status and event database summary</p>
          </div>
        </div>
        <button className="icon-btn" onClick={load} disabled={loading} title="Refresh">
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="alert-error">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      <div className="profile-grid">
        {/* Event DB card */}
        <div className="info-card">
          <div className="info-card-header">
            <Database size={18} className="info-card-icon cyan" />
            <span>Event Database</span>
          </div>
          <div className="big-stat">{loading ? '—' : events.length}</div>
          <div className="stat-sublabel">{isOfflineRules ? 'saved simulator events on this phone' : 'recorded notification events'}</div>
          <div className="info-card-detail">
            {events.length > 0 && (
              <>
                <div className="detail-row">
                  <span className="detail-key">Latest event</span>
                  <span className="detail-val mono">
                    {new Date(events[0].timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Most recent app</span>
                  <span className="detail-val">{events[0].source_app}</span>
                </div>
              </>
            )}
            {events.length === 0 && !loading && (
              <p className="muted-note">No saved events yet. Use the Notification Simulator to add an example.</p>
            )}
          </div>
        </div>

        {/* Model card */}
        <div className="info-card">
          <div className="info-card-header">
            <Brain size={18} className="info-card-icon indigo" />
            <span>{isOfflineRules ? 'On-device Decision Engine' : 'Action-Aware Model'}</span>
          </div>
          {loading ? (
            <div className="muted-note">Loading…</div>
          ) : modelStatus?.model_loaded ? (
            <>
              <div className="big-stat accent-green">Ready</div>
              <div className="stat-sublabel">{modelStatus.model_name ?? 'Unknown model'}</div>
              <div className="info-card-detail">
                {modelStatus.accuracy != null && (
                  <div className="detail-row">
                    <span className="detail-key">Accuracy</span>
                    <span className="detail-val mono">{(modelStatus.accuracy * 100).toFixed(1)}%</span>
                  </div>
                )}
                {modelStatus.roc_auc != null && (
                  <div className="detail-row">
                    <span className="detail-key">ROC-AUC</span>
                    <span className="detail-val mono">{modelStatus.roc_auc.toFixed(4)}</span>
                  </div>
                )}
                {modelStatus.training_samples != null && (
                  <div className="detail-row">
                    <span className="detail-key">Trained on</span>
                    <span className="detail-val mono">{modelStatus.training_samples.toLocaleString()} samples</span>
                  </div>
                )}
                {modelStatus.feature_count != null && (
                  <div className="detail-row">
                    <span className="detail-key">Features</span>
                    <span className="detail-val mono">{modelStatus.feature_count}</span>
                  </div>
                )}
                {modelStatus.target && (
                  <div className="detail-row">
                    <span className="detail-key">Target</span>
                    <span className="detail-val mono">{modelStatus.target}</span>
                  </div>
                )}
              </div>
            </>
          ) : isOfflineRules ? (
            <>
              <div className="big-stat accent-amber">Rules only</div>
              <div className="stat-sublabel">No trained personal model on this phone</div>
              <div className="info-card-detail"><p className="muted-note">Offline guidance uses conservative rules. It does not claim to predict your behavior.</p></div>
            </>
          ) : (
            <>
              <div className="big-stat accent-amber">Not Loaded</div>
              <div className="muted-note">Model artifact unavailable. Run training script.</div>
            </>
          )}
        </div>

        {/* Data provenance card */}
        <div className="info-card">
          <div className="info-card-header">
            <Cpu size={18} className="info-card-icon amber" />
            <span>Data Provenance</span>
          </div>
          <div className="big-stat" style={{ fontSize: '1rem', lineHeight: 1.4 }}>
            {isOfflineRules ? 'On-device' : 'Synthetic'}
          </div>
          <div className="stat-sublabel">{isOfflineRules ? 'local-only history' : 'development dataset'}</div>
          <div className="info-card-detail">
            {modelStatus?.data_provenance ? (
              <p className="muted-note" style={{ marginTop: 0 }}>{modelStatus.data_provenance}</p>
            ) : (
              <p className="muted-note" style={{ marginTop: 0 }}>
                Model trained on 8,000 synthetic events (10 simulated users, 14 days, seed=42).
                Predictions are model simulations — not verified real-world outcomes.
              </p>
            )}
            <div className="disclaimer-box">
              {isOfflineRules
                ? 'Offline guidance is rule-based. Personal learning needs real observed outcomes, which are not collected by this screen yet.'
                : 'Counterfactual predictions are not causal. They reflect patterns in synthetic training data only.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
