package io.zer0.muse.auth

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OAuthCallbackGuardTest {
    @Test
    fun acceptsOnlyMatchingNonEmptyState() {
        assertTrue(OAuthCallbackGuard.matchesPendingState("secret-state", "secret-state"))
        assertFalse(OAuthCallbackGuard.matchesPendingState("wrong-state", "secret-state"))
        assertFalse(OAuthCallbackGuard.matchesPendingState("secret-state", "other-state"))
    }

    @Test
    fun ignoresUnsolicitedOrMalformedCallbacks() {
        assertFalse(OAuthCallbackGuard.matchesPendingState(null, "secret-state"))
        assertFalse(OAuthCallbackGuard.matchesPendingState("", "secret-state"))
        assertFalse(OAuthCallbackGuard.matchesPendingState(" ", "secret-state"))
        assertFalse(OAuthCallbackGuard.matchesPendingState("secret-state", null))
        assertFalse(OAuthCallbackGuard.matchesPendingState("secret-state", ""))
        assertFalse(OAuthCallbackGuard.matchesPendingState("", ""))
    }
}
