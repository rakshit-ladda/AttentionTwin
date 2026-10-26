package com.attentiontwin.app;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

final class FocusScheduler {
    private static final int BREAK_REQUEST_CODE = 4817;
    private static final int WINDOW_REQUEST_CODE = 4819;
    private FocusScheduler() { }

    static void scheduleNext(Context context) {
        long next = FocusUtils.nextBreakAt(context);
        if (next != Long.MAX_VALUE) {
            Intent intent = new Intent(context, BreakReceiver.class).setAction("com.attentiontwin.BREAK");
            PendingIntent pending = PendingIntent.getBroadcast(context, BREAK_REQUEST_CODE, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (manager != null) {
                if (Build.VERSION.SDK_INT >= 23) manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next, pending);
                else manager.set(AlarmManager.RTC_WAKEUP, next, pending);
            }
        }
        scheduleFocusEnd(context);
        scheduleWindowTransition(context);
    }

    private static void scheduleWindowTransition(Context context) {
        long next = FocusUtils.nextFocusWindowTransition(context);
        Intent intent = new Intent(context, BreakReceiver.class).setAction("com.attentiontwin.FOCUS_WINDOW");
        PendingIntent pending = PendingIntent.getBroadcast(context, WINDOW_REQUEST_CODE, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;
        if (next == Long.MAX_VALUE) { manager.cancel(pending); return; }
        if (Build.VERSION.SDK_INT >= 23) manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next, pending);
        else manager.set(AlarmManager.RTC_WAKEUP, next, pending);
    }

    static void scheduleFocusEnd(Context context) {
        long end = FocusUtils.focusUntil(context);
        Intent intent = new Intent(context, BreakReceiver.class).setAction("com.attentiontwin.FOCUS_END");
        PendingIntent pending = PendingIntent.getBroadcast(context, BREAK_REQUEST_CODE + 1, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;
        if (end <= System.currentTimeMillis() || end == Long.MAX_VALUE) { manager.cancel(pending); return; }
        if (Build.VERSION.SDK_INT >= 23) manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, end, pending);
        else manager.set(AlarmManager.RTC_WAKEUP, end, pending);
    }
}
