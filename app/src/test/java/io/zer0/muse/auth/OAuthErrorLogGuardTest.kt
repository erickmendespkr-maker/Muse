package io.zer0.muse.auth

import org.junit.Assert.assertEquals
import org.junit.Test

class OAuthErrorLogGuardTest {
    @Test
    fun acceptsOnlyKnownStandardCodes() {
        listOf("invalid_request", "invalid_grant", "access_denied", "authorization_pending", "slow_down", "expired_token", "network_error").forEach {
            assertEquals(it, OAuthErrorLogGuard.safeCode(it))
        }
    }

    @Test
    fun hidesArbitraryProviderContent() {
        listOf(null, "", "invalid_grant\nBearer SECRET", "token=SECRET", "../invalid_grant", "INVALID_GRANT", " invalid_grant", "unknown_error", "https://evil.example/?code=SECRET").forEach {
            assertEquals("unrecognized_error", OAuthErrorLogGuard.safeCode(it))
        }
    }
}
