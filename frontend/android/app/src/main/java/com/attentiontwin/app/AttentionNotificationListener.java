package com.attentiontwin.app;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.content.SharedPreferences;
import android.os.Build;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;
import java.util.Calendar;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** Stores privacy-minimized notification lifecycle metadata locally. */
public class AttentionNotificationListener extends NotificationListenerService {
    static final String PREFS = "attention_twin_notification_metadata";
    static final String EVENTS = "events";
    static volatile boolean connected = false;
    static volatile AttentionNotificationListener instance;
    private static final Object LOCK = new Object();
    private static final int MAX_EVENTS = 200;
    private static final int MAX_TRANSITIONS_PER_EVENT = 32;
    private final Map<String, String> activeSystemKeys = new ConcurrentHashMap<>();
    private final Map<String, Long> deferredUntilById = new ConcurrentHashMap<>();

    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        connected = true;
        instance = this;
        try {
            StatusBarNotification[] active = getActiveNotifications();
            if (active != null) {
                for (StatusBarNotification sbn : active) {
                    if (sbn != null) activeSystemKeys.put(stableId(sbn.getKey()), sbn.getKey());
                }
            }
        } catch (RuntimeException ignored) {
            // Keep the listener usable if the platform cannot provide the initial active snapshot.
        }
    }

    @Override
    public void onListenerDisconnected() {
        connected = false;
        if (instance == this) instance = null;
        super.onListenerDisconnected();
    }

    @Override
    public void onDestroy() {
        connected = false;
        if (instance == this) instance = null;
        super.onDestroy();
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null) return;
        activeSystemKeys.put(stableId(sbn.getKey()), sbn.getKey());
        upsert(sbn, "active", null);
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        if (sbn == null) return;
        activeSystemKeys.remove(stableId(sbn.getKey()));
        upsert(sbn, "removed", null);
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn, RankingMap rankingMap, int reason) {
        if (sbn == null) return;
        activeSystemKeys.remove(stableId(sbn.getKey()));
        String state = Build.VERSION.SDK_INT >= 26 && reason == NotificationListenerService.REASON_SNOOZED
            ? "deferred" : "removed";
        upsert(sbn, state, reason);
    }

    boolean snooze(String id, long durationMs) {
        if (Build.VERSION.SDK_INT < 26) return false;
        String key = activeSystemKeys.get(id);
        if (key == null) return false;
        try {
            deferredUntilById.put(id, System.currentTimeMillis() + durationMs);
            snoozeNotification(key, durationMs);
            return true;
        } catch (RuntimeException ignored) {
            deferredUntilById.remove(id);
            return false;
        }
    }

    boolean snoozeUntilNextBreak(String id) {
        if (Build.VERSION.SDK_INT < 26) return false;
        String key = activeSystemKeys.get(id);
        if (key == null) return false;
        String schedule = getSharedPreferences(PREFS, MODE_PRIVATE).getString("break_times", "");
        long now = System.currentTimeMillis();
        long nextBreak = Long.MAX_VALUE;
        for (String value : schedule.split(",")) {
            String[] parts = value.trim().split(":");
            if (parts.length != 2) continue;
            try {
                int hour = Integer.parseInt(parts[0]);
                int minute = Integer.parseInt(parts[1]);
                if (hour < 0 || hour > 23 || minute < 0 || minute > 59) continue;
                Calendar candidate = Calendar.getInstance();
                candidate.set(Calendar.HOUR_OF_DAY, hour);
                candidate.set(Calendar.MINUTE, minute);
                candidate.set(Calendar.SECOND, 0);
                candidate.set(Calendar.MILLISECOND, 0);
                if (candidate.getTimeInMillis() <= now) candidate.add(Calendar.DAY_OF_YEAR, 1);
                nextBreak = Math.min(nextBreak, candidate.getTimeInMillis());
            } catch (NumberFormatException ignored) {
                // Ignore malformed locally stored values.
            }
        }
        long duration = nextBreak - now;
        if (nextBreak == Long.MAX_VALUE || duration <= 0 || duration > 24L * 60L * 60L * 1000L) return false;
        return snooze(id, duration);
    }

    private void upsert(StatusBarNotification sbn, String state, Integer reason) {
        try {
            String id = stableId(sbn.getKey());
            long now = System.currentTimeMillis();
            SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
            synchronized (LOCK) {
                JSONArray current = new JSONArray(prefs.getString(EVENTS, "[]"));
                JSONArray updated = new JSONArray();
                boolean found = false;
                for (int i = 0; i < current.length(); i++) {
                    JSONObject item = current.optJSONObject(i);
                    if (item == null) continue;
                    if (id.equals(item.optString("id"))) {
                        item.put("state", state);
                        item.put("updatedAt", now);
                        if ("active".equals(state)) {
                            item.remove("removedAt");
                            item.remove("removalReason");
                            item.remove("deferredUntil");
                            deferredUntilById.remove(id);
                        } else {
                            item.put("removedAt", now);
                            if (reason != null) item.put("removalReason", reason);
                            Long releaseAt = deferredUntilById.get(id);
                            if ("deferred".equals(state) && releaseAt != null) item.put("deferredUntil", releaseAt);
                        }
                        appendTransition(item, state, now, reason);
                        updated.put(item);
                        found = true;
                    } else {
                        updated.put(item);
                    }
                }
                if (!found) {
                    JSONObject item = new JSONObject();
                    item.put("id", id);
                    item.put("packageName", sbn.getPackageName());
                    item.put("postedAt", sbn.getPostTime());
                    item.put("updatedAt", now);
                    item.put("state", state);
                    item.put("clearable", sbn.isClearable());
                    if (reason != null) item.put("removalReason", reason);
                    Long releaseAt = deferredUntilById.get(id);
                    if ("deferred".equals(state) && releaseAt != null) item.put("deferredUntil", releaseAt);
                    appendTransition(item, state, now, reason);
                    updated.put(item);
                }
                int start = Math.max(0, updated.length() - MAX_EVENTS);
                JSONArray bounded = new JSONArray();
                for (int i = start; i < updated.length(); i++) bounded.put(updated.get(i));
                prefs.edit().putString(EVENTS, bounded.toString()).apply();
            }
        } catch (JSONException | RuntimeException ignored) {
            // Notification callbacks must never crash the system-bound listener.
        }
    }

    private static void appendTransition(JSONObject item, String state, long at, Integer reason) throws JSONException {
        JSONArray transitions = item.optJSONArray("transitions");
        if (transitions == null) transitions = new JSONArray();
        JSONObject transition = new JSONObject();
        transition.put("state", state);
        transition.put("at", at);
        if (reason != null) transition.put("reason", reason);
        transitions.put(transition);
        JSONArray bounded = new JSONArray();
        int start = Math.max(0, transitions.length() - MAX_TRANSITIONS_PER_EVENT);
        for (int i = start; i < transitions.length(); i++) bounded.put(transitions.get(i));
        item.put("transitions", bounded);
    }

    private static String stableId(String key) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(key.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (int i = 0; i < 16; i++) hex.append(String.format("%02x", digest[i]));
            return hex.toString();
        } catch (Exception ignored) {
            return UUID.nameUUIDFromBytes(key.getBytes(StandardCharsets.UTF_8)).toString();
        }
    }
}
