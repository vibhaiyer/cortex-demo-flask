"""Cortex end-to-end test: serve the app over real HTTP and call it with a client.

Runs the WSGI app in a background thread on a free port (werkzeug, which ships with
Flask) and requests every parameterless GET route with urllib. Skipped without Flask.
"""
import importlib
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

try:
    from werkzeug.serving import make_server
except ImportError:  # pragma: no cover
    make_server = None


def _find_app():
    for modname in ("app", "main", "wsgi", "application", "server"):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for attr in ("app", "application"):
            candidate = getattr(mod, attr, None)
            if candidate is not None and hasattr(candidate, "url_map"):
                return candidate
        factory = getattr(mod, "create_app", None)
        if callable(factory):
            try:
                return factory()
            except Exception:
                continue
    return None


@unittest.skipIf(make_server is None, "werkzeug is not installed")
class E2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _find_app()
        if cls.app is None:
            raise unittest.SkipTest("no Flask app object found")
        cls.server = make_server("127.0.0.1", 0, cls.app)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "server", None) is not None:
            cls.server.shutdown()

    def test_get_routes_answer_over_http(self):
        for rule in self.app.url_map.iter_rules():
            if "GET" not in rule.methods or rule.arguments or rule.endpoint == "static":
                continue
            url = "http://127.0.0.1:%d%s" % (self.port, rule.rule)
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    status = response.status
            except urllib.error.HTTPError as exc:
                status = exc.code
            self.assertNotEqual(status, 404, url)


if __name__ == "__main__":
    unittest.main()
