"""Cortex lint test: every source file compiles with warnings treated as errors.

Catches syntax errors, invalid escape sequences and similar issues without a linter
install. CI additionally runs ruff's error-class rules (see the cortex-ci workflow).
"""
import os
import unittest
import warnings

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP = {".git", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"}


class LintTest(unittest.TestCase):
    def test_sources_compile_cleanly(self):
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(base, name)
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    compile(source, path, "exec")

    def test_no_tabs_mixed_with_spaces(self):
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
            for name in files:
                if name.endswith(".py"):
                    path = os.path.join(base, name)
                    with open(path, encoding="utf-8") as fh:
                        for number, line in enumerate(fh, 1):
                            indent = line[: len(line) - len(line.lstrip())]
                            self.assertFalse("\t" in indent and " " in indent, "%s:%d" % (path, number))


if __name__ == "__main__":
    unittest.main()
