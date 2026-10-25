# AttentionTwin demo guide (current verified scope)

This guide demonstrates the offline dashboard, labeled synthetic demo data, local notification history, and opt-in background snooze. It does not demonstrate pre-display interception, personal ML learning, or verified behavior on every Android/OEM version.

1. Start the backend from the repository root: `.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000` (PowerShell).
2. In another terminal, run `npm run dev` from `frontend`.
3. Open the Vite URL. Confirm the health banner reports the backend state.
4. In the counterfactual screen, use the simulator to create a fictional social notification during a deep-work context.
5. Explain that the open probability is produced by a model trained on synthetic labels. The browsing/resumption fields are rule-based category/focus assumptions, and the defer time is currently fixed. Do not call the shown alternatives causal or personal predictions.
6. Open History to show backend event/decision records only if the selected event was actually submitted and saved.

For an Android build that has been successfully packaged and installed, grant notification access in the on-device panel and send a harmless test notification from another app. The panel should log only the source package and lifecycle metadata. Configure a near-future daily break time, then tap **Defer to break** on an active event to request Android system snoozing. This still requires physical-device verification before claiming OS behavior; snooze is not proof that the first alert was blocked or that repost timing is exact.

Use the latest `AttentionTwin-offline-debug.apk` from the Gradle output directory. No laptop backend is required for offline mode. The current debug APK requests notification access and may be blocked by Play Protect when sideloaded. Do not describe phone behavior as verified until the exact phone tests below pass.
