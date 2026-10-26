# AttentionTwin phone demo

## What is implemented

The Android app now has an on-device Capacitor bridge, a `NotificationListenerService`, a SQLite event store, focus timers, scheduled break digests, an optional locally stored preview setting, app importance roles, a rule-based action engine, and a separate 14-day synthetic-data mode. The original dashboard is available from **Settings → Open original AttentionTwin Lab screens**. Native notification history is kept in the app's private database; message title/text are evaluated in memory and are not stored by default.

The browser build uses localStorage and a TypeScript copy of the decision rules. It is a demo and cannot observe phone notifications or run when the browser is closed.

## Install and verify on Android

1. Build with `cd frontend && npm run build`, then `cd frontend/android && ./gradlew testDebugUnitTest assembleDebug` (use an Android SDK configured in `local.properties`).
2. Transfer `frontend/android/app/build/outputs/apk/debug/app-debug.apk` to the phone. Install it as an update over the existing AttentionTwin debug install where possible; Android rejects an update signed with a different key. A debug APK is intended for testing, not Play Store distribution.
3. Open AttentionTwin and complete setup. Enable its entry under **Settings → Notification access**. Xiaomi/HyperOS may require confirming a restricted setting from the app details screen.
4. Allow AttentionTwin to post notifications. In phone app settings, allow background/autostart and set battery use to unrestricted if HyperOS stops it.
5. In **Settings → App importance**, verify WhatsApp, Instagram, and Gmail are set to **Block in focus**. Change any app to **Allow** or **Smart** if desired. Break times default to 10:30, 13:00 and 15:30; edit them to match your schedule.
6. To suppress sound/vibration/heads-up before Android displays an alert, enable **Silence alerts during focus**, tap **Grant Do Not Disturb access**, and allow AttentionTwin in Android's notification-policy settings. This temporarily allows starred callers and alarms; AttentionTwin saves and restores the previous filter/policy. If you do not grant access, notification snoozing can still allow a brief banner flash.
7. Open **Live → Send a test** and test WhatsApp, Instagram, then Gmail. Each local test follows the Android listener path. Check its decision in **Settings → Diagnostics** and Inbox. Test events are labeled `test` and do not train real app statistics. For device logs, use `adb logcat -s AttentionTwin`.
8. Start focus, leave the app, and have a friend send “hello” on WhatsApp. Expect it to be snoozed until the next break and listed in Inbox. Repeat with DND on and off to see the brief-banner limitation. Calls, alarms, OTPs, urgent words, and VIP names are exceptions.
9. Check lock-screen behavior, reboot, force-stop/reopen, Xiaomi Autostart and battery restrictions. Android/OEM behavior requires this physical-device verification. Snoozed notifications cannot be returned early by AttentionTwin.
10. Load demo data in **Insights** only when you want sample charts. The banner labels it as synthetic, and **Remove demo** deletes only those rows.

## Important limits

Android notification access is a sensitive special permission; Play Protect may block an APK shared over WhatsApp. Do not disable device protection just to install a test build. If Google Play Protect blocks it, use Android Studio/ADB for a development install or distribute through a trusted internal testing channel. The debug APK uses a development signing key. A production release needs a user-controlled release key and a package signature compatible with the installed build.

Notification snoozing is supported by Android 8+ and OEM timing can differ. Android may create the notification before the listener callback snoozes it, so without DND the first alert can flash briefly. Snoozed notifications return at their scheduled time and cannot be released early by this app. WhatsApp retains message content; blocking only hides its alert. Focus/background behavior, DND restoration, notification access prompts, Play Protect, and Xiaomi HyperOS autostart/battery behavior still require real-phone testing; none are claimed as physically verified here.
