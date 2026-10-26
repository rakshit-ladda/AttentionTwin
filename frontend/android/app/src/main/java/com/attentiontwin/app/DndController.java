package com.attentiontwin.app;

import android.app.NotificationManager;
import android.content.Context;
import android.os.Build;

/** Temporarily applies a narrow priority filter and restores the user's saved DND state. */
final class DndController {
    private static final int ALLOW_CATEGORIES = NotificationManager.Policy.PRIORITY_CATEGORY_CALLS
        | NotificationManager.Policy.PRIORITY_CATEGORY_ALARMS;
    private static final int SUPPRESS_EFFECTS = NotificationManager.Policy.SUPPRESSED_EFFECT_PEEK
        | NotificationManager.Policy.SUPPRESSED_EFFECT_STATUS_BAR
        | NotificationManager.Policy.SUPPRESSED_EFFECT_NOTIFICATION_LIST
        | NotificationManager.Policy.SUPPRESSED_EFFECT_FULL_SCREEN_INTENT
        | NotificationManager.Policy.SUPPRESSED_EFFECT_LIGHTS
        | NotificationManager.Policy.SUPPRESSED_EFFECT_AMBIENT
        | NotificationManager.Policy.SUPPRESSED_EFFECT_BADGE;

    private DndController() { }

    static boolean hasAccess(Context context) {
        if (Build.VERSION.SDK_INT < 23) return false;
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        return manager != null && manager.isNotificationPolicyAccessGranted();
    }

    static void reconcile(Context context) {
        if (Build.VERSION.SDK_INT < 23) return;
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        if (!FocusUtils.prefs(context).getBoolean("silence_alerts", false) || !FocusUtils.isFocusActive(context)) {
            restore(context, manager);
            return;
        }
        if (!manager.isNotificationPolicyAccessGranted()) return;
        android.content.SharedPreferences prefs = FocusUtils.prefs(context);
        if (!prefs.getBoolean("dnd_saved", false)) {
            NotificationManager.Policy old = manager.getNotificationPolicy();
            prefs.edit()
                .putInt("dnd_filter", manager.getCurrentInterruptionFilter())
                .putInt("dnd_categories", old == null ? 0 : old.priorityCategories)
                .putInt("dnd_call_senders", old == null ? NotificationManager.Policy.PRIORITY_SENDERS_ANY : old.priorityCallSenders)
                .putInt("dnd_message_senders", old == null ? NotificationManager.Policy.PRIORITY_SENDERS_ANY : old.priorityMessageSenders)
                .putInt("dnd_effects", old == null || Build.VERSION.SDK_INT < 28 ? 0 : old.suppressedVisualEffects)
                .putBoolean("dnd_saved", true).apply();
        }
        try {
            manager.setNotificationPolicy(policy(ALLOW_CATEGORIES,
                NotificationManager.Policy.PRIORITY_SENDERS_STARRED,
                NotificationManager.Policy.PRIORITY_SENDERS_ANY, SUPPRESS_EFFECTS));
            manager.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_PRIORITY);
        } catch (SecurityException ignored) { }
    }

    private static void restore(Context context, NotificationManager manager) {
        android.content.SharedPreferences prefs = FocusUtils.prefs(context);
        if (!prefs.getBoolean("dnd_saved", false) || !manager.isNotificationPolicyAccessGranted()) return;
        try {
            manager.setNotificationPolicy(policy(
                prefs.getInt("dnd_categories", 0),
                prefs.getInt("dnd_call_senders", NotificationManager.Policy.PRIORITY_SENDERS_ANY),
                prefs.getInt("dnd_message_senders", NotificationManager.Policy.PRIORITY_SENDERS_ANY),
                prefs.getInt("dnd_effects", 0)));
            manager.setInterruptionFilter(prefs.getInt("dnd_filter", NotificationManager.INTERRUPTION_FILTER_ALL));
            prefs.edit().remove("dnd_saved").apply();
        } catch (SecurityException ignored) { }
    }

    private static NotificationManager.Policy policy(int categories, int callSenders, int messageSenders, int effects) {
        if (Build.VERSION.SDK_INT >= 28) return new NotificationManager.Policy(categories, callSenders, messageSenders, effects);
        return new NotificationManager.Policy(categories, callSenders, messageSenders);
    }
}
