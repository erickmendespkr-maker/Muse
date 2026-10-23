package io.zer0.muse.automation.vdisplay

import android.os.IBinder
import io.mockk.every
import io.mockk.mockk
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class VirtualDisplayBinderRegistryTest {
    @Before
    fun setUp() {
        VirtualDisplayBinderRegistry.clearHandoffToken()
        VirtualDisplayBinderRegistry.update(null)
    }

    @After
    fun tearDown() {
        VirtualDisplayBinderRegistry.clearHandoffToken()
        VirtualDisplayBinderRegistry.update(null)
    }

    @Test
    fun unsolicitedHandoffIsRejected() {
        assertFalse(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), "unsolicited"))
        assertFalse(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), null))
    }

    @Test
    fun incorrectTokenDoesNotConsumeValidToken() {
        VirtualDisplayBinderRegistry.setExpectedHandoffToken("expected-token")
        assertFalse(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), "wrong-token"))
        val validBinder = mockk<IBinder> {
            every { isBinderAlive } returns true
        }
        assertTrue(VirtualDisplayBinderRegistry.accept(validBinder, "expected-token"))
        assertSame(validBinder, VirtualDisplayBinderRegistry.current())
    }

    @Test
    fun successfulHandoffCannotBeReplayedOrReplaced() {
        VirtualDisplayBinderRegistry.setExpectedHandoffToken("one-time-token")
        val original = mockk<IBinder> {
            every { isBinderAlive } returns true
        }
        assertTrue(VirtualDisplayBinderRegistry.accept(original, "one-time-token"))
        assertFalse(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), "one-time-token"))
        assertSame(original, VirtualDisplayBinderRegistry.current())
    }

    @Test
    fun newLaunchCanAuthorizeAnotherHandoff() {
        VirtualDisplayBinderRegistry.setExpectedHandoffToken("first")
        assertTrue(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), "first"))
        VirtualDisplayBinderRegistry.setExpectedHandoffToken("second")
        assertTrue(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), "second"))
    }


    @Test
    fun pollingBeforeHandoffDoesNotRevokePendingToken() {
        val manager = VirtualDisplayServerManager(
            mockk<android.content.Context>(relaxed = true),
            mockk<io.zer0.muse.automation.core.AutomationManager>(relaxed = true),
        )
        VirtualDisplayBinderRegistry.setExpectedHandoffToken("pending-startup")
        repeat(3) { assertNull(manager.existingLiveProxy()) }
        val binder = mockk<IBinder> {
            every { isBinderAlive } returns true
        }
        assertTrue(VirtualDisplayBinderRegistry.accept(binder, "pending-startup"))
        assertSame(binder, VirtualDisplayBinderRegistry.current())
    }

    @Test
    fun clearingTokenRevokesPendingHandoff() {
        VirtualDisplayBinderRegistry.setExpectedHandoffToken("expired")
        VirtualDisplayBinderRegistry.clearHandoffToken()
        assertFalse(VirtualDisplayBinderRegistry.accept(mockk<IBinder>(), "expired"))
    }
}
