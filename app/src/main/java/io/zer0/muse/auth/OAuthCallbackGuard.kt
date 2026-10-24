package io.zer0.muse.auth

/** Prevent exported OAuth callback intents from altering unrelated login flows. */
internal object OAuthCallbackGuard {
    fun matchesPendingState(callbackState: String?, pendingState: String?): Boolean =
        !callbackState.isNullOrBlank() && !pendingState.isNullOrBlank() && callbackState == pendingState
}
