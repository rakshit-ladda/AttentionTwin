# AttentionTwin execution log

Updated: 2026-10-26

## Verified baseline

- Repository is `master` at `107fb98`, tracking `origin/master`; the configured remote is `https://github.com/rakshit-ladda/AttentionTwin.git`.
- The worktree was already dirty before this task. It contains `all_issues.json`, `crisis_repo/`, issue-scraping HTML/Python files, and several `upstream_*.ts` files. These are left untouched. No tracked changes were present at the start.
- `.gitignore` excludes `.env`, local databases, virtual environments, Node build output, and Android build output. Tracked files include two scikit-learn `.joblib` artifacts; no `.env` file or APK is tracked.
- The checked-in synthetic feature table has 8,000 rows and 23 columns, 10 simulated users, and the two targets `opened_within_5min` and `outcome_label`. It does not contain browsing duration, resumption delay, or interruption-duration columns. The raw synthetic JSON generator does create those duration fields, but these are simulated targets, not observed human data.
- Android is a Capacitor 8 / Java shell targeting SDK 36 (min SDK 24). This execution added an opt-in `NotificationListenerService`, Capacitor plugin, and local metadata panel. The listener stores package and lifecycle metadata only, with a 200-event cap and transition trail. The user can configure up to 12 local daily break times and manually snooze an active notification until the next one on API 26+. Android controls repost timing. There is no automatic policy routing or offline inference.
- The React app checks a remote FastAPI health endpoint and the README instructs phone users to configure a laptop URL. The phone runtime therefore has a laptop/network dependency.
- `backend/app/ml/counterfactual_engine.py` uses hard-coded category browsing times, focus-mode resumption times, a fixed 25-minute deferral, and a heuristic recommendation policy. The ML model predicts only prompt opening; it does not establish causal effects for unchosen actions.
- A debug APK exists at `frontend/android/app/build/outputs/apk/debug/app-debug.apk` (4,503,437 bytes), but this audit has not rebuilt or installed it. No configured `JAVA_HOME`, `ANDROID_HOME`, or attached device was found during the initial environment check.

## Research findings

- Public `NotificationListenerService` access requires the user to grant notification access. Public `snoozeNotification(key, durationMs)` is available from API 26, and the system posts a callback again when snoozing expires. The callback-driven listener is not a pre-post interception hook; it cannot promise prevention of the original first alert. OEM behavior also needs device testing.
- Notification Assistant / ranking adjustments are separate platform APIs with special system role/binding considerations; they are not evidence that an ordinary app can silently take over the system's notification pipeline.
- NotiFilter is currently available through F-Droid, is GPL-3.0-only, and documents notification access, filtering, snoozing/delay, local history, and offline operation. It is a reference, not a dependency or source to copy.
- The AmI-2018 GitHub dataset documents 176,195 notifications from 14 users (2018-05-07 to 2018-06-05), with package, post/removal time and device/alert state, but no direct app-session duration or task-resumption labels. Its repository declares GPL-3.0.
- The AmI-2019 GitHub dataset documents 229,792 notifications from 44 users (2018-12-19 to 2019-05-03), with post/removal times, package/device state and venue fields. It does not provide the target interruption duration/resumption labels; combining it with another dataset cannot create per-person joins. Its README permits use and requests citation; verify repository license text before redistribution.
- UbiqLog is a broader lifelog/app-use source, not a notification-response dataset suitable for training the response target without further verified notification-level labels. Its source repository declares BSD-2-Clause; the historical UCI dataset itself has a privacy-use restriction and must be checked before reuse.

## Work completed in this execution

- Follow-up milestone: Android no longer requires a laptop backend when the backend URL is blank. Added an on-device fallback for health, counterfactual comparison, event history, and profile status. Offline event rows omit user-entered message text; they use WebView local storage. If a configured backend is unreachable, these calls fall back to local mode.
- Offline counterfactual output is explicitly rule-based, with no fabricated user opening probability or time estimates. It recommends only conservative guidance; DEFER remains an explicit user action and SUPPRESS is comparison-only.
- Frontend TypeScript production build passed; Capacitor sync passed; Gradle `assembleDebug` passed in WSL. Output `frontend/android/app/build/outputs/apk/debug/AttentionTwin-offline-debug.apk` is signed with the existing Windows debug key. Physical-device install/run remains blocked/unverified: the user's screenshot shows Google Play Protect blocking the sideloaded APK because of sensitive notification access.
- Remaining acceptance gap: there is still no on-device personal model, no longitudinal learning, no Room database, and no physical-device verification. The native listener is post-publication and cannot guarantee suppression of the first alert. An opt-in package/window rule can now snooze selected notifications after posting, but this needs device validation.
- Latest fast-turn milestone: added opt-in Android background snoozing for user-selected app packages during explicit focus windows. Calls, alarms, reminders, error/navigation categories, system notifications, and non-clearable notifications are skipped. Automatic deferral requires a saved break schedule and remains off by default. Added a 24-event synthetic demo pack to the offline profile; it is labeled and removable, with only simulated summary metrics.
- Verification: frontend build, Capacitor sync, Gradle `assembleDebug`, and APK v2 signature verification passed. Physical-device listener callback behavior and Play Protect installation remain unverified.
- Physical-device checklist now includes the opt-in background rule, category exceptions, first-alert limitation, and synthetic demo data cleanup. All device cases remain not run.
- Follow-up: local profile/history now merges the native listener's bounded notification metadata with locally saved simulator examples. It derives tap/dismiss/snooze outcome labels from Android's reported removal reason and retained state transitions. It still stores no notification body, and it does not infer browsing duration, task-resumption, importance, or fatigue.
- Verification after outcome integration: `npm run build`, `npx cap sync android`, and WSL Gradle `assembleDebug` passed; the APK signature verifies against the Windows debug certificate. Device callbacks, Play Protect installation, and app behavior on the user's phone remain unverified.

- Repository, Git state, source structure, ignore rules, existing API/model/data and Android configuration inspected.
- Android API and dataset/reference-app research started using primary Android documentation and dataset/project sources.
- Frontend production build completed successfully after native UI integration (`npm run build`); Vite emitted a non-fatal large-chunk advisory (main JS bundle 582.82 kB).
- Backend suite initially stalled because Windows asyncio could not create a TestClient socketpair inside the sandbox. Running the full suite with escalation passed all 39 tests in 4.77s (one Starlette/httpx deprecation warning). A separate synthetic-only run also passed 5 tests.
- The new Java listener, Capacitor plugin, and activity compiled with `javac` against the installed Android 36 and cached Capacitor/AndroidX classpaths. This catches Java compile errors but does not replace Gradle packaging, Android instrumentation, or OS callback testing.
- Android Gradle build was attempted repeatedly, including escalated retries with IPv4 and single-worker settings. A direct JDK selector probe reproduces `Unable to establish loopback connection` outside the sandbox (JDK 21.0.4), so the current JDK cannot start Gradle's daemon. Existing APK remains the artifact from 2026-10-25; no new APK was produced. No physical device is attached/tested.
- Documentation and README audit were committed as `d49f432` and `eaae308`. Native implementation and follow-up documentation changes are uncommitted. No push was made.

## Remaining work

This is a multi-phase engineering mission and remains incomplete. A first native metadata listener and user-triggered next-break snooze are implemented in source, but still need APK packaging and device verification. Remaining work includes automatic decision routing, exact/reboot-resilient delivery guarantees, offline decision/runtime, dataset license/schema follow-up, broader UI redesign, honest model evaluation, instrumentation/device testing, and rebuilding the APK. Physical Redmi/HyperOS behavior cannot be claimed without that device.

## Exact next action

Use an alternate supported JDK if available (or resolve the JDK 21 Windows selector loopback issue), then run Gradle packaging. After that, install on a test phone and validate listener permission, posted/removed events, configured break time parsing, and system snooze/repost. Do not claim first-alert suppression, automatic decisions, or exact-time delivery.
