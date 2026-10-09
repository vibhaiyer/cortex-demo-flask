"""Cortex integration tests: the web app boots and its routes answer over the WSGI stack.

Uses the framework's own test client, so no server is started. Skipped when Flask is not
installed or no app object can be found.
"""
import importlib
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

try:
    import flask  # noqa: F401
except ImportError:  # pragma: no cover
    flask = None


def _find_app():
    for modname in ("app", "main", "wsgi", "application", "server"):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for attr in ("app", "application"):
            candidate = getattr(mod, attr, None)
            if candidate is not None and hasattr(candidate, "test_client"):
                return candidate
        factory = getattr(mod, "create_app", None)
        if callable(factory):
            try:
                return factory()
            except Exception:
                continue
    return None


@unittest.skipIf(flask is None, "flask is not installed")
class AppIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = _find_app()
        if self.app is None:
            self.skipTest("no Flask app object found (app, create_app, wsgi, ...)")
        self.app.config["TESTING"] = True
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        self.client = self.app.test_client()

    def test_app_registers_routes(self):
        rules = [r for r in self.app.url_map.iter_rules() if r.endpoint != "static"]
        self.assertTrue(rules, "the app registers no routes")

    def test_parameterless_get_routes_respond(self):
        for rule in self.app.url_map.iter_rules():
            if "GET" not in rule.methods or rule.arguments or rule.endpoint == "static":
                continue
            response = self.client.get(rule.rule)
            self.assertIsNotNone(response.status_code, rule.rule)
            self.assertNotEqual(response.status_code, 404, "%s is registered but 404s" % rule.rule)

    def test_unknown_route_is_404(self):
        self.assertEqual(self.client.get("/__cortex_no_such_route__").status_code, 404)


if __name__ == "__main__":
    unittest.main()
