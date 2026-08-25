"""Regression tests for the add-on's response to HTTP 401 ingress errors.

Background
----------
After a Home Assistant restart, the supervisor may return HTTP 401 when the
add-on sidebar panel tries to load. This is a known HA bug where the ingress
panel does not re-register its auth token after a Core restart. The add-on
itself is healthy; the failure is on the HA side.

The fix is purely front-end: when any API call returns 401, we render a
dedicated "Session Expired" error page that explains the situation and
offers the documented workarounds (refresh, re-toggle sidebar, log out
and back in). These tests verify the JS source contains the 401 handling
in the three places that fetch the API.
"""

import json
import re
import unittest
from pathlib import Path


WEB_SERVER_JS = Path(__file__).resolve().parent.parent / "ha_sentry" / "rootfs" / "app" / "web_server.py"


class TestIngress401Handling(unittest.TestCase):
    """Verify the front-end has dedicated 401 handling in all API call sites."""

    @classmethod
    def setUpClass(cls):
        cls.web_server_text = WEB_SERVER_JS.read_text(encoding="utf-8")

    def _has_401_branch(self, search_region):
        return "401" in search_region and (
            "Session Expired" in search_region
            or "ingress session" in search_region.lower()
        )

    def test_initial_status_check_has_401_branch(self):
        m = re.search(
            r"const statusResponse = await fetchWithTimeout\(statusUrl.*?if \(!statusResponse\.ok\)",
            self.web_server_text,
            re.DOTALL,
        )
        self.assertIsNotNone(
            m,
            "Could not locate the initial status check in web_server.py",
        )
        region = self.web_server_text[m.start():m.end() + 4000]
        self.assertTrue(
            self._has_401_branch(region),
            "Initial status check has no dedicated 401 handling",
        )

    def test_status_poll_has_401_branch(self):
        m = re.search(
            r"async function pollBuildStatus\(\).*?return new Promise",
            self.web_server_text,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "pollBuildStatus() not found")
        region = self.web_server_text[m.start():m.start() + 6000]
        self.assertTrue(
            self._has_401_branch(region),
            "Status poll loop has no dedicated 401 handling",
        )

    def test_components_fetch_has_401_branch(self):
        m = re.search(
            r"const componentsUrl = getApiUrl\('api/components'\).*?STEP 4: Parse and validate",
            self.web_server_text,
            re.DOTALL,
        )
        self.assertIsNotNone(
            m,
            "Could not locate the components fetch in web_server.py",
        )
        region = self.web_server_text[m.start():m.end()]
        self.assertTrue(
            self._has_401_branch(region),
            "Components fetch has no dedicated 401 handling",
        )

    def test_401_error_references_known_ha_bug(self):
        self.assertIn(
            "known Home Assistant bug",
            self.web_server_text,
            "401 error should mention this is a known Home Assistant bug",
        )

    def test_401_error_offers_refresh_workaround(self):
        self.assertIn("Refresh Page", self.web_server_text)
        self.assertIn("Show in sidebar", self.web_server_text)
        self.assertIn("log out of Home Assistant", self.web_server_text)


class TestPanelAdminUnchanged(unittest.TestCase):
    """The fix must not weaken panel_admin: true security setting."""

    def test_panel_admin_true_in_yaml(self):
        yaml_path = Path(__file__).resolve().parent.parent / "ha_sentry" / "config.yaml"
        text = yaml_path.read_text(encoding="utf-8")
        match = re.search(r"^\s*panel_admin:\s*true\s*$", text, re.MULTILINE)
        self.assertIsNotNone(match, "panel_admin: true not found in config.yaml")

    def test_panel_admin_true_in_json(self):
        json_path = Path(__file__).resolve().parent.parent / "ha_sentry" / "config.json"
        data = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertTrue(data.get("panel_admin"))


if __name__ == "__main__":
    unittest.main()
