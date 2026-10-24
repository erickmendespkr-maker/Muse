package io.zer0.muse.auth

/**
 * Never pass an OAuth provider's arbitrary `error` or `error_description` to logs/UI.
 * A malicious or misconfigured endpoint can echo codes, credentials and line breaks.
 * Only standardized, fixed error codes may be displayed.
 */
internal object OAuthErrorLogGuard {
    private val knownCodes = setOf(
        "invalid_request", "invalid_client", "invalid_grant", "unauthorized_client",
        "unsupported_grant_type", "invalid_scope", "access_denied",
        "authorization_pending", "slow_down", "expired_token", "server_error",
        "temporarily_unavailable", "network_error",
    )

    fun safeCode(untrusted: String?): String =
        if (untrusted != null && untrusted in knownCodes) untrusted else "unrecognized_error"
}
