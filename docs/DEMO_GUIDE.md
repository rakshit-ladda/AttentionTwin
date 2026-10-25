# AttentionTwin demo guide (current verified scope)

This guide demonstrates the existing dashboard and synthetic comparison only. It does not demonstrate live phone notification interception, automatic deferral, offline phone inference, or personalization from real observations.

1. Start the backend from the repository root: ` .venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000` (PowerShell).
2. In another terminal, run `npm run dev` from `frontend`.
3. Open the Vite URL. Confirm the health banner reports the backend state.
4. In the counterfactual screen, use the simulator to create a fictional social notification during a deep-work context.
5. Explain that the open probability is produced by a model trained on synthetic labels. The browsing/resumption fields are rule-based category/focus assumptions, and the defer time is currently fixed. Do not call the shown alternatives causal or personal predictions.
6. Open History to show backend event/decision records only if the selected event was actually submitted and saved.

The existing debug APK can be installed for a UI-only demonstration, but the app will need a reachable FastAPI backend configured in Settings. The APK was not rebuilt in this audit. No device behavior should be demonstrated as verified unless tested on that device.
