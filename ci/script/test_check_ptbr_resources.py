"""Regression tests for complete pt-BR Android resource coverage."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_ptbr_resources as checker


class PtBrResourceCoverageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.res = Path(self.temp.name)
        for locale in ("values", "values-en", "values-pt-rBR"):
            folder = self.res / locale
            folder.mkdir()
            (folder / "strings.xml").write_text(
                '<resources><string name="hello">Hello</string></resources>', encoding="utf-8"
            )
            (folder / "automation_strings.xml").write_text(
                '<resources><string name="auto_label">Automation</string></resources>',
                encoding="utf-8",
            )
            (folder / "automation_tasker_strings.xml").write_text(
                '<resources><string name="tasker_label">Tasker</string></resources>',
                encoding="utf-8",
            )
        (self.res / "xml").mkdir()
        (self.res / "xml/locales_config.xml").write_text(
            '<locale-config xmlns:android="http://schemas.android.com/apk/res/android">'
            '<locale android:name="pt-BR" /></locale-config>',
            encoding="utf-8",
        )

    def run_checker(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(checker, "RES", self.res), contextlib.redirect_stdout(out), \
             contextlib.redirect_stderr(err):
            result = checker.main()
        return result, out.getvalue(), err.getvalue()

    def test_automation_resources_are_collected(self):
        strings, errors = checker.read_strings(self.res / "values-pt-rBR")
        self.assertFalse(errors)
        self.assertEqual({"hello", "auto_label", "tasker_label"}, set(strings))

    def test_complete_automation_resources_pass(self):
        result, output, errors = self.run_checker()
        self.assertEqual(0, result, errors)
        self.assertIn("pt-BR=3", output)

    def test_missing_automation_translation_fails(self):
        (self.res / "values-pt-rBR/automation_strings.xml").write_text(
            "<resources />", encoding="utf-8"
        )
        result, _, errors = self.run_checker()
        self.assertEqual(1, result)
        self.assertIn("auto_label", errors)

    def test_automation_placeholder_mismatch_fails(self):
        (self.res / "values-en/automation_strings.xml").write_text(
            '<resources><string name="auto_label">Run %1$s</string></resources>',
            encoding="utf-8",
        )
        (self.res / "values-pt-rBR/automation_strings.xml").write_text(
            '<resources><string name="auto_label">Executar %1$d</string></resources>',
            encoding="utf-8",
        )
        result, _, errors = self.run_checker()
        self.assertEqual(1, result)
        self.assertIn("Format mismatch for auto_label", errors)

    def test_duplicate_key_across_file_families_fails(self):
        (self.res / "values-pt-rBR/strings.xml").write_text(
            '<resources><string name="hello">Oi</string>'
            '<string name="auto_label">Duplicado</string></resources>',
            encoding="utf-8",
        )
        result, _, errors = self.run_checker()
        self.assertEqual(1, result)
        self.assertIn("Duplicate key auto_label", errors)


if __name__ == "__main__":
    unittest.main()
