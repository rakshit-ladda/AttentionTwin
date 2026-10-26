package com.attentiontwin.app;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.provider.Settings;
import android.text.TextUtils;
import java.util.Calendar;
import java.util.Locale;

final class FocusUtils {
    static final String PREFS = "attentiontwin_focus";
    private FocusUtils() { }

    static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    static boolean hasNotificationAccess(Context context) {
        String enabled = Settings.Secure.getString(context.getContentResolver(), "enabled_notification_listeners");
        return !TextUtils.isEmpty(enabled) && enabled.contains(new ComponentName(context, FocusListenerService.class).flattenToString());
    }

    static boolean isFocusActive(Context context) {
        long until = prefs(context).getLong("focus_until", 0L);
        return until == Long.MAX_VALUE || until > System.currentTimeMillis() || inDailyWindow(context);
    }

    static long focusUntil(Context context) {
        return prefs(context).getLong("focus_until", 0L);
    }

    static boolean inDailyWindow(Context context) {
        String schedule = prefs(context).getString("focus_schedule", "");
        int now = Calendar.getInstance().get(Calendar.HOUR_OF_DAY) * 60 + Calendar.getInstance().get(Calendar.MINUTE);
        for (String item : schedule.split(",")) {
            String[] parts = item.trim().split("-");
            if (parts.length != 2) continue;
            int start = parseTime(parts[0]);
            int end = parseTime(parts[1]);
            if (start < 0 || end < 0 || start == end) continue;
            if (start < end ? now >= start && now < end : now >= start || now < end) return true;
        }
        return false;
    }

    static long nextBreakAt(Context context) {
        String times = prefs(context).getString("break_times", "10:30,13:00,15:30");
        long now = System.currentTimeMillis();
        long next = Long.MAX_VALUE;
        for (String value : times.split(",")) {
            int minutes = parseTime(value);
            if (minutes < 0) continue;
            Calendar candidate = Calendar.getInstance();
            candidate.set(Calendar.HOUR_OF_DAY, minutes / 60);
            candidate.set(Calendar.MINUTE, minutes % 60);
            candidate.set(Calendar.SECOND, 0);
            candidate.set(Calendar.MILLISECOND, 0);
            if (candidate.getTimeInMillis() <= now) candidate.add(Calendar.DAY_OF_YEAR, 1);
            next = Math.min(next, candidate.getTimeInMillis());
        }
        return next;
    }

    static int minutesToBreak(Context context) {
        long next = nextBreakAt(context);
        if (next == Long.MAX_VALUE) return 25;
        return Math.max(1, (int) Math.ceil((next - System.currentTimeMillis()) / 60000.0));
    }

    static String roleFor(Context context, String packageName) {
        String stored = prefs(context).getString("role_" + packageName, null);
        if (stored != null) return stored;
        if ("com.instagram.android".equals(packageName)) return DecisionEngine.Role.DISTRACTING.name();
        return DecisionEngine.Role.NORMAL.name();
    }

    static String categoryFor(String packageName, String label) {
        String value = ((packageName == null ? "" : packageName) + " " + (label == null ? "" : label)).toLowerCase(Locale.ROOT);
        if (value.contains("instagram") || value.contains("youtube") || value.contains("tiktok") || value.contains("facebook") || value.contains("linkedin")) return "social";
        if (value.contains("whatsapp") || value.contains("telegram") || value.contains("messenger") || value.contains("slack") || value.contains("gmail") || value.contains("mail")) return "communication";
        if (value.contains("calendar") || value.contains("notion") || value.contains("docs") || value.contains("github") || value.contains("outlook")) return "work";
        if (value.contains("bank") || value.contains("pay") || value.contains("health")) return "health";
        if (value.contains("system") || value.contains("phone") || value.contains("dialer")) return "system";
        return "other";
    }

    static int parseTime(String value) {
        String[] parts = value.trim().split(":");
        if (parts.length != 2) return -1;
        try {
            int h = Integer.parseInt(parts[0]);
            int m = Integer.parseInt(parts[1]);
            return h < 0 || h > 23 || m < 0 || m > 59 ? -1 : h * 60 + m;
        } catch (NumberFormatException ignored) { return -1; }
    }
}
