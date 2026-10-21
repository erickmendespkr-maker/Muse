package io.zer0.muse.intent

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Source-level regression tests for the Tasker broadcast cost guard.
 * The receiver additionally serializes reservation of the accepted slot.
 */
class TaskerTriggerGuardTest {
    @Test
    fun disabledRejectsRequests() {
        assertEquals(
            TaskerTriggerGuard.Decision.REJECTED_DISABLED,
            TaskerTriggerGuard.evaluate(
                enabled = false,
                promptLength = 10,
                nowMs = 10_000L,
                lastAcceptedAtMs = null,
            ),
        )
    }

    @Test
    fun emptyAndOversizedPromptsAreRejected() {
        assertEquals(
            TaskerTriggerGuard.Decision.REJECTED_BLANK,
            TaskerTriggerGuard.evaluate(
                enabled = true,
                promptLength = 0,
                nowMs = 10_000L,
                lastAcceptedAtMs = null,
            ),
        )
        assertEquals(
            TaskerTriggerGuard.Decision.REJECTED_TOO_LONG,
            TaskerTriggerGuard.evaluate(
                enabled = true,
                promptLength = TaskerTriggerGuard.MAX_PROMPT_LENGTH + 1,
                nowMs = 10_000L,
                lastAcceptedAtMs = null,
            ),
        )
    }

    @Test
    fun rapidRepeatedRequestsAreThrottled() {
        val acceptedAt = 10_000L
        assertEquals(
            TaskerTriggerGuard.Decision.REJECTED_THROTTLED,
            TaskerTriggerGuard.evaluate(
                enabled = true,
                promptLength = 10,
                nowMs = acceptedAt + TaskerTriggerGuard.MIN_INTERVAL_MS - 1,
                lastAcceptedAtMs = acceptedAt,
            ),
        )
        assertEquals(
            TaskerTriggerGuard.Decision.ACCEPTED,
            TaskerTriggerGuard.evaluate(
                enabled = true,
                promptLength = 10,
                nowMs = acceptedAt + TaskerTriggerGuard.MIN_INTERVAL_MS,
                lastAcceptedAtMs = acceptedAt,
            ),
        )
    }

    @Test
    fun initialRequestIsAccepted() {
        assertEquals(
            TaskerTriggerGuard.Decision.ACCEPTED,
            TaskerTriggerGuard.evaluate(
                enabled = true,
                promptLength = TaskerTriggerGuard.MAX_PROMPT_LENGTH,
                nowMs = 10_000L,
                lastAcceptedAtMs = null,
            ),
        )
    }
}
