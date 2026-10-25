package com.attentiontwin.app;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.content.SharedPreferences;
import android.os.Build;
import android.app.Notification;
import android.text.TextUtils;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;
import java.util.Calendar;
import java.util.Set;
import java.util.HashSet;
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
    private final Map<String, String> deferredOriginById = new ConcurrentHashMap<>();
    private final Set<String> autoDeferAttempted = ConcurrentHashMap.newKeySet();

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
        maybeAutoDefer(sbn);
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
        if (!"deferred".equals(state)) autoDeferAttempted.remove(stableId(sbn.getKey()));
    }

    boolean snoozeUntilNextBreak(String id) {
        return snoozeUntilNextBreak(id, "user");
    }

    private boolean snoozeUntilNextBreak(String id, String origin) {
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
        return snooze(id, duration, origin);
    }

    private boolean snooze(String id, long durationMs, String origin) {
        if (Build.VERSION.SDK_INT < 26) return false;
        String key = activeSystemKeys.get(id);
        if (key == null) return false;
        try {
            deferredUntilById.put(id, System.currentTimeMillis() + durationMs);
            deferredOriginById.put(id, origin);
            snoozeNotification(key, durationMs);
            return true;
        } catch (RuntimeException ignored) {
            deferredUntilById.remove(id);
            deferredOriginById.remove(id);
            return false;
        }
    }

    private void maybeAutoDefer(StatusBarNotification sbn) {
        String id = stableId(sbn.getKey());
        boolean inFocusWindow = isInConfiguredFocusWindow();
        if (!inFocusWindow) autoDeferAttempted.remove(id);
        if (Build.VERSION.SDK_INT < 26 || !sbn.isClearable() || !inFocusWindow) return;
        Notification notification = sbn.getNotification();
        if (notification == null || isProtectedCategory(notification.category)) return;

        String packageName = sbn.getPackageName();
        if (TextUtils.isEmpty(packageName) || packageName.equals(getPackageName())
            || "android".equals(packageName) || "com.android.systemui".equals(packageName)) return;

        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        if (!prefs.getBoolean("auto_defer_enabled", false)) return;
        Set<String> selectedPackages = csvSet(prefs.getString("auto_defer_packages", ""));
        if (!selectedPackages.contains(packageName)) return;

        if (!autoDeferAttempted.add(id)) return;
        if (!snoozeUntilNextBreak(id, "automatic")) autoDeferAttempted.remove(id);
    }

    private boolean isInConfiguredFocusWindow() {
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        String[] windows = prefs.getString("focus_windows", "").split(",");
        Calendar now = Calendar.getInstance();
        int current = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE);
        for (String window : windows) {
            String[] parts = window.trim().split("-");
            if (parts.length != 2) continue;
            int start = parseTime(parts[0]);
            int end = parseTime(parts[1]);
            if (start < 0 || end < 0 || start == end) continue;
            if (start < end ? current >= start && current < end : current >= start || current < end) return true;
        }
        return false;
    }

    private static int parseTime(String value) {
        String[] parts = value.trim().split(":");
        if (parts.length != 2) return -1;
        try {
            int hour = Integer.parseInt(parts[0]);
            int minute = Integer.parseInt(parts[1]);
            if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return -1;
            return hour * 60 + minute;
        } catch (NumberFormatException ignored) {
            return -1;
        }
    }

    private static Set<String> csvSet(String csv) {
        Set<String> values = new HashSet<>();
        for (String value : csv.split(",")) {
            String trimmed = value.trim();
            if (!trimmed.isEmpty()) values.add(trimmed);
        }
        return values;
    }

    private static boolean isProtectedCategory(String category) {
        return Notification.CATEGORY_CALL.equals(category)
            || Notification.CATEGORY_ALARM.equals(category)
            || Notification.CATEGORY_REMINDER.equals(category)
            || Notification.CATEGORY_ERROR.equals(category)
            || Notification.CATEGORY_NAVIGATION.equals(category);
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
                        if (!item.has("appLabel")) item.put("appLabel", applicationLabel(sbn.getPackageName()));
                        item.put("state", state);
                        item.put("updatedAt", now);
                        if ("active".equals(state)) {
                            item.remove("removedAt");
                            item.remove("removalReason");
                            item.remove("deferredUntil");
                            item.remove("deferOrigin");
                            deferredUntilById.remove(id);
                            deferredOriginById.remove(id);
                        } else {
                            item.put("removedAt", now);
                            if (reason != null) item.put("removalReason", reason);
                            Long releaseAt = deferredUntilById.get(id);
                            if ("deferred".equals(state) && releaseAt != null) item.put("deferredUntil", releaseAt);
                            String origin = deferredOriginById.get(id);
                            if ("deferred".equals(state) && origin != null) item.put("deferOrigin", origin);
                        }
                        appendTransition(item, state, now, reason, deferredOriginById.get(id));
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
                    item.put("appLabel", applicationLabel(sbn.getPackageName()));
                    item.put("postedAt", sbn.getPostTime());
                    item.put("updatedAt", now);
                    item.put("state", state);
                    item.put("clearable", sbn.isClearable());
                    if (reason != null) item.put("removalReason", reason);
                    Long releaseAt = deferredUntilById.get(id);
                    if ("deferred".equals(state) && releaseAt != null) item.put("deferredUntil", releaseAt);
                    String origin = deferredOriginById.get(id);
                    if ("deferred".equals(state) && origin != null) item.put("deferOrigin", origin);
                    appendTransition(item, state, now, reason, origin);
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

    private static void appendTransition(JSONObject item, String state, long at, Integer reason, String deferOrigin) throws JSONException {
        JSONArray transitions = item.optJSONArray("transitions");
        if (transitions == null) transitions = new JSONArray();
        JSONObject transition = new JSONObject();
        transition.put("state", state);
        transition.put("at", at);
        if (reason != null) transition.put("reason", reason);
        if ("deferred".equals(state) && deferOrigin != null) transition.put("deferOrigin", deferOrigin);
        transitions.put(transition);
        JSONArray bounded = new JSONArray();
        int start = Math.max(0, transitions.length() - MAX_TRANSITIONS_PER_EVENT);
        for (int i = start; i < transitions.length(); i++) bounded.put(transitions.get(i));
        item.put("transitions", bounded);
    }

    private String applicationLabel(String packageName) {
        try {
            android.content.pm.ApplicationInfo info = getPackageManager().getApplicationInfo(packageName, 0);
            CharSequence label = getPackageManager().getApplicationLabel(info);
            return label == null ? packageName : label.toString();
        } catch (Exception ignored) {
            return packageName;
        }
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
