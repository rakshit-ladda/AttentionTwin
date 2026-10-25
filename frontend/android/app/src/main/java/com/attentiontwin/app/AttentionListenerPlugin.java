package com.attentiontwin.app;

import android.content.Intent;
import android.os.Build;
import android.provider.Settings;
import android.text.TextUtils;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.regex.Pattern;

@CapacitorPlugin(name = "AttentionListener")
public class AttentionListenerPlugin extends Plugin {
    private boolean hasNotificationAccess() {
        String enabled = Settings.Secure.getString(
            getContext().getContentResolver(), "enabled_notification_listeners"
        );
        if (TextUtils.isEmpty(enabled)) return false;
        for (String component : enabled.split(":")) {
            if (component.startsWith(getContext().getPackageName() + "/")) return true;
        }
        return false;
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject result = new JSObject();
        result.put("accessGranted", hasNotificationAccess());
        result.put("connected", AttentionNotificationListener.connected);
        result.put("preDisplayInterception", false);
        call.resolve(result);
    }

    @PluginMethod
    public void requestAccess(PluginCall call) {
        try {
            getActivity().startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
            call.resolve();
        } catch (Exception error) {
            call.reject("Could not open Android notification access settings", error);
        }
    }

    @PluginMethod
    public void getEvents(PluginCall call) {
        String saved = getContext()
            .getSharedPreferences(AttentionNotificationListener.PREFS, 0)
            .getString(AttentionNotificationListener.EVENTS, "[]");
        try {
            JSObject result = new JSObject();
            result.put("events", new JSArray(saved));
            call.resolve(result);
        } catch (Exception error) {
            call.reject("Could not read local notification metadata", error);
        }
    }

    @PluginMethod
    public void clearHistory(PluginCall call) {
        getContext().getSharedPreferences(AttentionNotificationListener.PREFS, 0)
            .edit().remove(AttentionNotificationListener.EVENTS).apply();
        call.resolve();
    }

    @PluginMethod
    public void getBreakSchedule(PluginCall call) {
        String times = getContext().getSharedPreferences(AttentionNotificationListener.PREFS, 0)
            .getString("break_times", "");
        JSObject result = new JSObject();
        result.put("times", times);
        call.resolve(result);
    }

    @PluginMethod
    public void saveBreakSchedule(PluginCall call) {
        String times = call.getString("times", "").trim();
        if (!times.isEmpty()) {
            String[] entries = times.split(",");
            if (entries.length > 12) {
                call.reject("Enter no more than 12 daily break times");
                return;
            }
            for (String entry : entries) {
                if (!Pattern.matches("(?:[01]\\d|2[0-3]):[0-5]\\d", entry.trim())) {
                    call.reject("Use 24-hour times such as 10:30, 13:00");
                    return;
                }
            }
        }
        getContext().getSharedPreferences(AttentionNotificationListener.PREFS, 0)
            .edit().putString("break_times", times).apply();
        call.resolve();
    }

    @PluginMethod
    public void deferUntilNextBreak(PluginCall call) {
        if (Build.VERSION.SDK_INT < 26) {
            call.reject("System notification snoozing requires Android 8.0 or newer");
            return;
        }
        String id = call.getString("id");
        if (id == null || id.isEmpty()) {
            call.reject("A notification event ID is required");
            return;
        }
        AttentionNotificationListener listener = AttentionNotificationListener.instance;
        if (listener == null || !listener.snoozeUntilNextBreak(id)) {
            call.reject("No upcoming break is configured, this notification is no longer active, or Android could not snooze it");
            return;
        }
        call.resolve();
    }
}
