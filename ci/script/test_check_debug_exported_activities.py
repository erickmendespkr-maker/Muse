"""Regression tests for debug-only exported-component policy."""
import contextlib
import io
import sys
import unittest
from unittest.mock import patch

import check_debug_exported_activities as checker


class DebugActivityPolicyTest(unittest.TestCase):
    def check(self, overrides=None):
        activities = {name: False for name in checker.TARGETS}
        activities.update(overrides or {})
        with patch.object(checker, "activities_from_apk", return_value=activities), \
             patch.object(sys, "argv", ["checker", "test.apk"]), \
             contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            return checker.main()

    def test_all_debug_components_private(self):
        self.assertEqual(0, self.check())

    def test_exported_leakcanary_launcher_rejected(self):
        self.assertEqual(1, self.check({"leakcanary.internal.activity.LeakLauncherActivity": True}))

    def test_exported_compose_test_activity_rejected(self):
        self.assertEqual(1, self.check({"androidx.activity.ComponentActivity": True}))

    def test_missing_component_rejected(self):
        self.assertEqual(1, self.check({"androidx.activity.ComponentActivity": "MISSING"}))


if __name__ == "__main__":
    unittest.main()
