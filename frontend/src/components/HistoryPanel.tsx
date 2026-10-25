/**
 * HistoryPanel — Phase 6
 * Displays recorded notification events from SQLite (/api/events)
 * and allows expanding an event to view full audit history (/api/events/{id}/history):
 * decisions, observed outcomes, counterfactual predictions, and feedback.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { 
  History, 
  RefreshCw, 
  ChevronRight, 
  ChevronDown, 
  AlertCircle, 
  CheckCircle, 
  FileText, 
  Clock,
  Sparkles,
  MessageSquare
} from 'lucide-react';
import { 
  api, 
  NotificationEventResponse, 
  EventHistoryResponse 
} from '../api';

export const HistoryPanel: React.FC = () => {
  const [events, setEvents] = useState<NotificationEventResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [historyData, setHistoryData] = useState<Record<number, EventHistoryResponse>>({});
  const [historyLoading, setHistoryLoading] = useState<number | null>(null);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listEvents(50, 0);
      setEvents(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const toggleEventExpand = async (eventId: number) => {
    if (selectedEventId === eventId) {
      setSelectedEventId(null);
      return;
    }
    setSelectedEventId(eventId);
    if (!historyData[eventId]) {
      setHistoryLoading(eventId);
      try {
        const hist = await api.getEventHistory(eventId);
        setHistoryData((prev) => ({ ...prev, [eventId]: hist }));
      } catch (err) {
        console.error('Failed to load history for event', eventId, err);
      } finally {
        setHistoryLoading(null);
      }
    }
  };

  return (
    <div className="live-section">
      <div className="section-header-bar">
        <div className="section-title-wrap">
          <div className="section-icon-large">
            <History size={22} />
          </div>
          <div>
            <h2 className="section-title">History and Learning</h2>
            <p className="section-tagline">
              Empirical interaction logs, logged decisions, counterfactual predictions, and user feedback
            </p>
          </div>
        </div>
        <button 
          className="icon-btn" 
          onClick={fetchEvents} 
          disabled={loading} 
          title="Refresh Events"
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="alert-error">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {loading && events.length === 0 ? (
        <div className="empty-state">
          <Clock size={32} className="spin" style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
          <p>Loading empirical event logs from local database...</p>
        </div>
      ) : events.length === 0 ? (
        <div className="empty-state">
          <FileText size={40} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
          <p>No events recorded in <code>attention_twin.db</code> yet.</p>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Use the <strong>Notification Simulator</strong> to test notifications and click &quot;Save Event to DB&quot;.
          </span>
        </div>
      ) : (
        <div className="events-table-card">
          <div className="events-table-header">
            <span style={{ fontWeight: 600 }}>Local Audit Trail ({events.length} events)</span>
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              attention_twin.db
            </span>
          </div>

          <div className="events-list">
            {events.map((evt) => {
              const isExpanded = selectedEventId === evt.id;
              const hist = historyData[evt.id];
              const isLoadingHist = historyLoading === evt.id;

              return (
                <div key={evt.id} className={`event-item-container ${isExpanded ? 'expanded' : ''}`}>
                  <div 
                    className="event-row-summary"
                    onClick={() => toggleEventExpand(evt.id)}
                  >
                    <div className="event-row-left">
                      <span className="expand-chevron">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </span>
                      <span className="event-id-badge">#{evt.id}</span>
                      <span className="event-app-chip">{evt.source_app}</span>
                      <span className="event-cat-chip">{evt.category}</span>
                      <span className="event-text-preview">{evt.text}</span>
                    </div>

                    <div className="event-row-right">
                      <span className="mono event-time">
                        {new Date(evt.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="event-history-details">
                      {isLoadingHist ? (
                        <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          Loading history records...
                        </div>
                      ) : hist ? (
                        <div className="history-subsections">
                          {/* Event Raw Context */}
                          {evt.context_data && Object.keys(evt.context_data).length > 0 && (
                            <div className="history-subblock">
                              <div className="subblock-title">Context Telemetry</div>
                              <pre className="subblock-code">
                                {JSON.stringify(evt.context_data, null, 2)}
                              </pre>
                            </div>
                          )}

                          {/* Decisions */}
                          <div className="history-subblock">
                            <div className="subblock-title">
                              Decisions ({hist.decisions.length})
                            </div>
                            {hist.decisions.length === 0 ? (
                              <div className="subblock-empty">No decision recorded yet for this event.</div>
                            ) : (
                              <div className="badge-row">
                                {hist.decisions.map((d) => (
                                  <div key={d.id} className="history-pill decision">
                                    <CheckCircle size={14} />
                                    <strong>{d.action.toUpperCase()}</strong>
                                    {d.reason && <span>&mdash; {d.reason}</span>}
                                    <span className="pill-time">{new Date(d.timestamp).toLocaleTimeString()}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Observed Outcomes */}
                          <div className="history-subblock">
                            <div className="subblock-title">
                              Observed Outcomes ({hist.observed_outcomes.length})
                            </div>
                            {hist.observed_outcomes.length === 0 ? (
                              <div className="subblock-empty">No observed outcomes logged yet.</div>
                            ) : (
                              <div className="badge-row">
                                {hist.observed_outcomes.map((o) => (
                                  <div key={o.id} className="history-pill outcome">
                                    <FileText size={14} />
                                    <strong>{o.outcome_type}</strong>
                                    {o.interaction_measurements && (
                                      <span>({JSON.stringify(o.interaction_measurements)})</span>
                                    )}
                                    <span className="pill-time">{new Date(o.timestamp).toLocaleTimeString()}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Counterfactual Predictions Saved */}
                          <div className="history-subblock">
                            <div className="subblock-title">
                              Recorded Counterfactual Predictions ({hist.counterfactual_predictions.length})
                            </div>
                            {hist.counterfactual_predictions.length === 0 ? (
                              <div className="subblock-empty">No stored predictions for this event record.</div>
                            ) : (
                              <div className="badge-row">
                                {hist.counterfactual_predictions.map((p) => (
                                  <div key={p.id} className="history-pill prediction">
                                    <Sparkles size={14} />
                                    <strong>Action: {p.proposed_action}</strong>
                                    <span>Outcome: {JSON.stringify(p.predicted_outcome)}</span>
                                    <span className="pill-time">v{p.model_version}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* User Feedback */}
                          <div className="history-subblock">
                            <div className="subblock-title">
                              User Feedback ({hist.feedback.length})
                            </div>
                            {hist.feedback.length === 0 ? (
                              <div className="subblock-empty">No feedback submitted.</div>
                            ) : (
                              <div className="badge-row">
                                {hist.feedback.map((f) => (
                                  <div key={f.id} className="history-pill feedback">
                                    <MessageSquare size={14} />
                                    {f.feedback_rating && <span>Rating: {f.feedback_rating}/5</span>}
                                    {f.feedback_label && <span>[{f.feedback_label}]</span>}
                                    {f.comment && <span>&ldquo;{f.comment}&rdquo;</span>}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div style={{ padding: '1rem', color: 'var(--accent-rose)' }}>
                          Failed to load event history.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
