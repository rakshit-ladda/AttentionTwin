# AttentionTwin execution log

Updated: 2026-10-26

## Verified baseline

- Repository is `master` at `107fb98`, tracking `origin/master`; the configured remote is `https://github.com/rakshit-ladda/AttentionTwin.git`.
- The worktree was already dirty before this task. It contains `all_issues.json`, `crisis_repo/`, issue-scraping HTML/Python files, and several `upstream_*.ts` files. These are left untouched. No tracked changes were present at the start.
- `.gitignore` excludes `.env`, local databases, virtual environments, Node build output, and Android build output. Tracked files include two scikit-learn `.joblib` artifacts; no `.env` file or APK is tracked.
- The checked-in synthetic feature table has 8,000 rows and 23 columns, 10 simulated users, and the two targets `opened_within_5min` and `outcome_label`. It does not contain browsing duration, resumption delay, or interruption-duration columns. The raw synthetic JSON generator does create those duration fields, but these are simulated targets, not observed human data.
- Android is a Capacitor 8 / Java shell targeting SDK 36 (min SDK 24). The manifest currently declares no notification listener, boot receiver, scheduler, or local data service. `MainActivity` only extends `BridgeActivity`.
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

- Repository, Git state, source structure, ignore rules, existing API/model/data and Android configuration inspected.
- Android API and dataset/reference-app research started using primary Android documentation and dataset/project sources.
- Python regression suite and frontend production build started; frontend build completed successfully with a Vite chunk-size advisory. Python suite was still running at last check and is not yet reported as passing.
- No source code or application behavior has been changed in this pass. No commit or push has been made.

## Remaining work

This is a multi-phase engineering mission and remains incomplete. In particular: finish evidence-backed dataset license/schema inventory; review additional apps and Android scheduling/privacy requirements; build native notification access with an honest post-post alternative; add local persistence and offline decision/runtime; redesign UI; train/evaluate only defensible models; implement tests and device checklist; rebuild APK; complete docs; run all required checks; then commit verified milestones. Physical Redmi/HyperOS behavior cannot be claimed without that device.

## Exact next action

Collect the running regression-suite result, then implement a first native notification-listener milestone only if the available Android toolchain can build it. Keep the initial milestone metadata-only and local, with explicit user-granted access and no claim that the original alert is prevented.
