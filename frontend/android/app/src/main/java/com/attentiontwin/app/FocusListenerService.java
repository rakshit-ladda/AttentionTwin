package com.attentiontwin.app;

import android.app.Notification;
import android.content.ComponentName;
import android.os.Build;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

/** System-bound listener: it continues receiving callbacks while the UI is closed. */
public final class FocusListenerService extends NotificationListenerService {
    public static volatile boolean connected = false;
    private Store store;
    private final DecisionEngine engine = new DecisionEngine();

    @Override public void onCreate() {
        super.onCreate();
        store = new Store(this);
    }

    @Override public void onListenerConnected() {
        super.onListenerConnected();
        connected = true;
    }

    @Override public void onListenerDisconnected() {
        connected = false;
        requestRebind(new ComponentName(this, FocusListenerService.class));
        super.onListenerDisconnected();
    }

    @Override public void onDestroy() {
        connected = false;
        if (store != null) store.close();
        super.onDestroy();
    }

    @Override public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || store == null) return;
        Notification notification = sbn.getNotification();
        if (notification == null || isNonActionable(notification)) return;

        Bundle extras = notification.extras;
        boolean isTest = extras != null && extras.getBoolean("at_test", false);
        String packageName = sbn.getPackageName();
        if (getPackageName().equals(packageName) && !isTest) return;
        if (isTest) packageName = extras.getString("at_fake_pkg", "com.instagram.android");

        String keyHash = keyHash(sbn.getKey());
        long now = System.currentTimeMillis();
        org.json.JSONObject existing = store.findByKey(keyHash);
        if (existing != null && "HELD".equals(existing.optString("state"))) {
            long releaseAt = existing.optLong("releaseAt", 0L);
            if (!DecisionEngine.shouldKeepHeldOnRepost(releaseAt, now)) {
                store.updateState(existing.optLong("id"), "RELEASED", 0L, "ALLOW", "The system re-posted the held notification at its scheduled release.");
                return;
            }
            long remaining = releaseAt - now;
            try { snoozeNotification(sbn.getKey(), remaining); }
            catch (RuntimeException ignored) { store.updateState(existing.optLong("id"), "RELEASED", 0L, "ALLOW", "Could not retain the early re-post; let it through."); }
            return;
        }

        if (store.findRecentByKey(keyHash, now - 4000L) != null) return;

        String label = applicationLabel(packageName);
        String title = extras == null ? "" : stringExtra(extras, Notification.EXTRA_TITLE);
        String body = extras == null ? "" : stringExtra(extras, Notification.EXTRA_TEXT);
        String channel = Build.VERSION.SDK_INT >= 26 ? safe(sbn.getNotification().getChannelId()) : "";
        String category = FocusUtils.categoryFor(packageName, label);
        String notificationCategory = safe(notification.category);
        String roleText = FocusUtils.roleFor(this, packageName);
        DecisionEngine.Role role;
        try { role = DecisionEngine.Role.valueOf(roleText); }
        catch (IllegalArgumentException ignored) { role = DecisionEngine.Role.NORMAL; }

        boolean focus = FocusUtils.isFocusActive(this);
        boolean keepPreviews = FocusUtils.prefs(this).getBoolean("keep_previews", false);
        String urgentWords = FocusUtils.prefs(this).getString("urgent_words", "");
        DecisionEngine.Input input = new DecisionEngine.Input();
        input.packageName = packageName;
        input.category = category;
        input.notificationCategory = notificationCategory;
        input.title = title;
        input.text = body;
        input.urgentWords = urgentWords;
        input.role = role;
        input.focusActive = focus;
        input.keepPreviews = keepPreviews;
        input.minutesToBreak = FocusUtils.minutesToBreak(this);
        input.stats = store.stats(packageName, isTest ? "test" : "real");

        DecisionEngine.Result result = engine.evaluate(input);
        DecisionEngine.Action action = result.action;
        String reason = result.reason;
        long releaseAt = 0L;
        if (action == DecisionEngine.Action.SUPPRESS && !keepPreviews) {
            action = DecisionEngine.Action.DEFER;
            reason = "Suppression requires Keep previews; safely falling back to deferral. " + reason;
        }
        if (action == DecisionEngine.Action.DEFER) {
            releaseAt = FocusUtils.nextBreakAt(this);
            if (Build.VERSION.SDK_INT < 26 || releaseAt == Long.MAX_VALUE || releaseAt <= now) {
                action = DecisionEngine.Action.ALLOW;
                reason = "No usable break time is configured; letting the notification through. " + reason;
                releaseAt = 0L;
            }
        }

        Store.Event event = new Store.Event();
        event.nkey = keyHash;
        event.pkg = packageName;
        event.label = label;
        event.category = category;
        event.channel = channel;
        event.ts = now;
        event.focus = focus;
        event.action = action.name();
        event.state = action == DecisionEngine.Action.DEFER ? "HELD"
            : action == DecisionEngine.Action.SUPPRESS ? "SUPPRESSED" : "SHOWN";
        event.reason = reason;
        event.pOpen = result.openRateEstimate;
        event.cAllow = result.allowCost;
        event.cDefer = result.deferCost;
        event.cSuppress = result.suppressCost;
        event.importance = result.importanceEstimate;
        event.releaseAt = releaseAt;
        event.source = isTest ? "test" : "real";
        event.exception = result.exception ? reason : "";
        if (action == DecisionEngine.Action.SUPPRESS && keepPreviews) event.preview = (title + "\n" + body).trim();
        long id;
        try { id = store.insert(event); }
        catch (RuntimeException ignored) { return; }
        store.incrementShown(packageName, event.source);

        try {
            if (action == DecisionEngine.Action.DEFER) {
                snoozeNotification(sbn.getKey(), releaseAt - now);
            } else if (action == DecisionEngine.Action.SUPPRESS) {
                cancelNotification(sbn.getKey());
            }
        } catch (RuntimeException error) {
            store.updateState(id, "SHOWN", 0L, "ALLOW", "Android rejected the action; left the notification available.");
        }
    }

    @Override public void onNotificationRemoved(StatusBarNotification sbn, RankingMap rankingMap, int reason) {
        if (sbn == null || store == null) return;
        String hash = keyHash(sbn.getKey());
        org.json.JSONObject event = store.findByKey(hash);
        if (event == null) return;
        if (reason == NotificationListenerService.REASON_CLICK) {
            store.markOpenedByKey(hash);
            return;
        }
        if ("SUPPRESSED".equals(event.optString("state")) || reason == NotificationListenerService.REASON_SNOOZED) return;
    }

    private boolean isNonActionable(Notification notification) {
        int flags = notification.flags;
        if ((flags & Notification.FLAG_GROUP_SUMMARY) != 0) return true;
        if ((flags & Notification.FLAG_ONGOING_EVENT) != 0 || (flags & Notification.FLAG_NO_CLEAR) != 0) return true;
        if (Build.VERSION.SDK_INT >= 26 && notification.getChannelId() == null) return true;
        String category = notification.category;
        return Notification.CATEGORY_SERVICE.equals(category)
            || Notification.CATEGORY_TRANSPORT.equals(category)
            || Notification.CATEGORY_CALL.equals(category)
            || Notification.CATEGORY_ALARM.equals(category)
            || Notification.CATEGORY_NAVIGATION.equals(category);
    }

    private String applicationLabel(String packageName) {
        try {
            android.content.pm.ApplicationInfo info = getPackageManager().getApplicationInfo(packageName, 0);
            CharSequence label = getPackageManager().getApplicationLabel(info);
            return label == null ? packageName : label.toString();
        } catch (Exception ignored) { return packageName; }
    }

    private static String stringExtra(Bundle extras, String key) {
        Object value = extras.get(key);
        return value == null ? "" : String.valueOf(value);
    }

    static String keyHash(String key) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(key.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (int i = 0; i < 16; i++) out.append(String.format(Locale.ROOT, "%02x", digest[i]));
            return out.toString();
        } catch (Exception ignored) { return Integer.toHexString(key.hashCode()); }
    }

    private static String safe(String value) { return value == null ? "" : value; }
}
