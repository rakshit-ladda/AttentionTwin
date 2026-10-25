import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Bell, ExternalLink, RefreshCw, Trash2 } from 'lucide-react';
import { attentionListener, LocalNotificationEvent, NotificationAccessStatus } from '../native/attentionListener';
import './NotificationAccessPanel.css';

const unavailableStatus: NotificationAccessStatus = {
  accessGranted: false,
  connected: false,
  preDisplayInterception: false,
};

export const NotificationAccessPanel: React.FC = () => {
  const [status, setStatus] = useState(unavailableStatus);
  const [events, setEvents] = useState<LocalNotificationEvent[]>([]);
  const [breakTimes, setBreakTimes] = useState('');
  const [breakScheduleConfigured, setBreakScheduleConfigured] = useState(false);
  const [scheduleSaved, setScheduleSaved] = useState(false);
  const scheduleDraftDirty = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [nextStatus, nextEvents, nextSchedule] = await Promise.all([
        attentionListener.getStatus(),
        attentionListener.getEvents(),
        attentionListener.getBreakSchedule(),
      ]);
      setStatus(nextStatus);
      setEvents([...nextEvents.events].reverse());
      setBreakScheduleConfigured(Boolean(nextSchedule.times.trim()));
      if (!scheduleDraftDirty.current) setBreakTimes(nextSchedule.times);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not read local notification access status.');
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), 3000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const requestAccess = async () => {
    setBusy(true);
    try {
      await attentionListener.requestAccess();
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not open Android notification settings.');
    } finally {
      setBusy(false);
      window.setTimeout(() => void refresh(), 1000);
    }
  };

  const clearHistory = async () => {
    setBusy(true);
    try {
      await attentionListener.clearHistory();
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not clear local history.');
    } finally {
      setBusy(false);
    }
  };

  const saveBreakSchedule = async () => {
    setBusy(true);
    try {
      await attentionListener.saveBreakSchedule({ times: breakTimes });
      scheduleDraftDirty.current = false;
      setBreakScheduleConfigured(Boolean(breakTimes.trim()));
      setScheduleSaved(true);
      await refresh();
      window.setTimeout(() => setScheduleSaved(false), 2000);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save break times.');
    } finally {
      setBusy(false);
    }
  };

  const deferUntilNextBreak = async (id: string) => {
    setBusy(true);
    try {
      await attentionListener.deferUntilNextBreak({ id });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Android could not snooze this notification.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="notification-access-panel" aria-labelledby="notification-access-title">
      <div className="notification-access-heading">
        <div className="notification-access-icon"><Bell size={18} /></div>
        <div className="notification-access-title-wrap">
          <h2 id="notification-access-title">On-device notification access</h2>
          <p>Metadata-only local history · no message text is saved</p>
        </div>
        <span className={`listener-state ${status.connected ? 'is-connected' : status.accessGranted ? 'is-waiting' : ''}`}>
          {status.connected ? 'Listening' : status.accessGranted ? 'Connecting' : 'Access off'}
        </span>
      </div>

      <p className="notification-access-explainer">
        Android lets AttentionTwin observe notifications after they are posted. Enabling access does not prevent the first banner, sound, or vibration.
      </p>

      <div className="notification-access-actions">
        {!status.accessGranted && (
          <button className="btn-primary" type="button" onClick={() => void requestAccess()} disabled={busy}>
            <ExternalLink size={14} /> Grant notification access
          </button>
        )}
        <button className="btn-secondary" type="button" onClick={() => void refresh()} disabled={busy}>
          <RefreshCw size={14} /> Refresh
        </button>
        {events.length > 0 && (
          <button className="btn-secondary" type="button" onClick={() => void clearHistory()} disabled={busy}>
            <Trash2 size={14} /> Clear local history
          </button>
        )}
      </div>

      <div className="notification-break-schedule">
        <label htmlFor="notification-break-times">Daily break times (24-hour, comma-separated)</label>
        <div className="notification-break-schedule-inputs">
          <input
            id="notification-break-times"
            type="text"
            value={breakTimes}
            onChange={(event) => {
              scheduleDraftDirty.current = true;
              setBreakTimes(event.target.value);
            }}
            placeholder="10:30, 13:00, 15:30"
            aria-describedby="notification-break-help"
          />
          <button className="btn-secondary" type="button" onClick={() => void saveBreakSchedule()} disabled={busy}>
            {scheduleSaved ? 'Saved' : 'Save breaks'}
          </button>
        </div>
        <p id="notification-break-help">System snooze releases a manually deferred notification at the next configured time. Android/Doze may affect exact delivery time.</p>
      </div>

      {error && <p className="notification-access-error" role="alert">{error}</p>}

      {events.length > 0 ? (
        <ul className="notification-event-list" aria-label="Recent local notification metadata">
          {events.slice(0, 5).map((event) => (
            <li key={event.id}>
              <span className="notification-event-app">{event.packageName}</span>
              <span className="notification-event-time">{new Date(event.postedAt).toLocaleString()}</span>
              <span className="notification-event-state">
                {event.state === 'deferred' && event.deferredUntil
                  ? `snoozed until ${new Date(event.deferredUntil).toLocaleTimeString()}`
                  : event.state}
              </span>
              {event.state === 'active' && status.connected && breakScheduleConfigured && (
                <button className="notification-event-defer" type="button" onClick={() => void deferUntilNextBreak(event.id)} disabled={busy}>
                  Defer to break
                </button>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="notification-access-empty">{status.accessGranted ? 'No notification metadata recorded yet.' : 'Grant access to begin local metadata logging.'}</p>
      )}
    </section>
  );
};
