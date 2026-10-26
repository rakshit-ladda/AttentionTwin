# AttentionTwin phone demo

## What is implemented

The Android app now has an on-device Capacitor bridge, a `NotificationListenerService`, a SQLite event store, focus timers, scheduled break digests, an optional locally stored preview setting, app importance roles, a rule-based action engine, and a separate 14-day synthetic-data mode. The original dashboard is available from **Settings → Open original AttentionTwin Lab screens**. Native notification history is kept in the app's private database; message title/text are evaluated in memory and are not stored by default.

The browser build uses localStorage and a TypeScript copy of the decision rules. It is a demo and cannot observe phone notifications or run when the browser is closed.

## Install and verify on Android

1. Build with `cd frontend && npm run build`, then `cd frontend/android && ./gradlew testDebugUnitTest assembleDebug` (use an Android SDK configured in `local.properties`).
2. Transfer `frontend/android/app/build/outputs/apk/debug/app-debug.apk` to the phone. Install it as an update over the existing AttentionTwin debug install where possible; Android rejects an update signed with a different key. A debug APK is intended for testing, not Play Store distribution.
3. Open AttentionTwin and complete setup. Enable its entry under **Settings → Notification access**. Xiaomi/HyperOS may require confirming a restricted setting from the app details screen.
4. Allow AttentionTwin to post notifications. In phone app settings, allow background/autostart and set battery use to unrestricted if HyperOS stops it.
5. In **Settings → App importance**, mark an app Important, Normal, or Distracting. Break times default to 10:30, 13:00 and 15:30; edit them to match your schedule.
6. Open **Live → Send a test**. The app posts a local test notification and the listener routes it through the rule engine. Observe the decision in activity/inbox. Test events remain marked `test` and do not train real app statistics.
7. Start a focus session, leave the app, and check that a permitted app's notification is deferred until a configured break. Also test a call/alarm/OTP notification and confirm it remains available.
8. Load demo data in **Insights** only when you want sample charts. The banner labels it as synthetic, and **Remove demo** deletes only those rows.

## Important limits

Android notification access is a sensitive special permission; Play Protect may block an APK shared over WhatsApp. Do not disable device protection just to install a test build. If Google Play Protect blocks it, use Android Studio/ADB for a development install or distribute through a trusted internal testing channel. The debug APK uses a development signing key. A production release needs a user-controlled release key and a package signature compatible with the installed build.

Notification snoozing is supported by Android 8+ and OEM timing can differ. Android may show an alert before the listener callback acts on it, so this is not guaranteed to prevent the first interruption. Focus/background behavior, notification access prompts, Play Protect, and Xiaomi HyperOS autostart/battery behavior still require a real phone test; they are not claimed as physically verified here.
