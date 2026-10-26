package com.attentiontwin.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class DecisionEngineTest {
    private final DecisionEngine engine = new DecisionEngine();

    @Test public void focusOffAlwaysAllows() {
        DecisionEngine.Input in = new DecisionEngine.Input(); in.focusActive = false; in.role = DecisionEngine.Role.DISTRACTING;
        assertEquals(DecisionEngine.Action.ALLOW, engine.evaluate(in).action);
    }
    @Test public void importantAppAlwaysAllows() {
        DecisionEngine.Input in = new DecisionEngine.Input(); in.focusActive = true; in.role = DecisionEngine.Role.IMPORTANT;
        assertEquals(DecisionEngine.Action.ALLOW, engine.evaluate(in).action);
    }
    @Test public void verificationCodeAlwaysAllows() {
        DecisionEngine.Input in = new DecisionEngine.Input(); in.focusActive = true; in.title = "Your verification code"; in.text = "Use 381902";
        DecisionEngine.Result result = engine.evaluate(in);
        assertEquals(DecisionEngine.Action.ALLOW, result.action); assertTrue(result.exception);
    }
    @Test public void urgentWordAlwaysAllows() {
        DecisionEngine.Input in = new DecisionEngine.Input(); in.focusActive = true; in.text = "Emergency: call now"; in.urgentWords = "emergency";
        assertEquals(DecisionEngine.Action.ALLOW, engine.evaluate(in).action);
    }
    @Test public void lowHistoryProtectsMeaningfulImportanceFromSuppression() {
        DecisionEngine.Input in = new DecisionEngine.Input(); in.focusActive = true; in.category = "communication"; in.role = DecisionEngine.Role.NORMAL;
        in.stats = new DecisionEngine.Stats(2, 0, 0, 0);
        assertNotEquals(DecisionEngine.Action.SUPPRESS, engine.evaluate(in).action);
    }
    @Test public void heldNotificationIsNotRejudgedUntilScheduledRelease() {
        assertTrue(DecisionEngine.shouldKeepHeldOnRepost(2000, 1000));
        assertFalse(DecisionEngine.shouldKeepHeldOnRepost(1000, 1000));
    }
    @Test public void openRateUsesEightObservationPrior() {
        DecisionEngine.Input in = new DecisionEngine.Input(); in.category = "social";
        in.stats = new DecisionEngine.Stats(0, 0, 0, 0);
        assertEquals(.62, engine.evaluate(in).openRateEstimate, .0001);
    }
}
