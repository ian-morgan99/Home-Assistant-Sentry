"""
Tests for the getApiUrl helper in web_server.py.
Uses a lightweight Node.js snippet to exercise the JS logic directly.
"""
import json
import subprocess
import sys
import os


def run_node_test():
    script = r"""
        global.window = { location: { pathname: '/api/hassio_ingress/ha_sentry', origin: 'http://localhost' } };
        function addDiagnosticLog() {}
        function getApiUrl(path) {
            const rawPath = path || '';
            let decodedPath = rawPath;
            try {
                decodedPath = decodeURIComponent(rawPath);
            } catch (e) {
                addDiagnosticLog('Failed to decode API path, using raw value', 'warning');
            }
            const traversalPattern = /(\.\.)|(%2e%2e)|(%252e%252e)/i;
            const match = traversalPattern.exec(rawPath) || traversalPattern.exec(decodedPath);
            if (match) {
                const message = `Unsafe API path detected: directory traversal pattern "${match[0]}" is not allowed in "${decodedPath}".`;
                addDiagnosticLog(message, 'error');
                throw new Error(message);
            }
            // Return relative URL - works with both direct access and HA ingress
            const sanitizedPath = decodedPath
                .replace(/^\/+/, '')
                .replace(/\/{2,}/g, '/');
            return sanitizedPath;
        }
        function run(name, fn) {
            try {
                return { name, value: fn(), error: null };
            } catch (e) {
                return { name, value: null, error: String(e.message || e) };
            }
        }
        const results = [];
        results.push(run('normal', () => getApiUrl('api/status')));
        results.push(run('leading-slash', () => getApiUrl('/api/components')));
        results.push(run('double-slash', () => getApiUrl('api//components')));
        results.push(run('traversal', () => getApiUrl('../etc/passwd')));
        results.push(run('encoded-traversal', () => getApiUrl('%2e%2e/api')));
        results.push(run('double-encoded-traversal', () => getApiUrl('%252e%252e/api')));
        console.log(JSON.stringify(results));
    """
    output = subprocess.check_output(["node", "-e", script], text=True)
    return json.loads(output.strip())


def test_get_api_url_paths():
    results = run_node_test()
    by_name = {r["name"]: r for r in results}

    # Now returns relative URLs (works with both direct and ingress access)
    assert by_name["normal"]["error"] is None
    assert by_name["normal"]["value"] == "api/status"

    assert by_name["leading-slash"]["error"] is None
    assert by_name["leading-slash"]["value"] == "api/components"

    assert by_name["double-slash"]["error"] is None
    assert by_name["double-slash"]["value"] == "api/components"

    # Traversal attempts should raise errors
    assert by_name["traversal"]["error"] is not None
    assert "Unsafe API path detected" in by_name["traversal"]["error"]

    assert by_name["encoded-traversal"]["error"] is not None
    assert by_name["double-encoded-traversal"]["error"] is not None


if __name__ == "__main__":
    try:
        test_get_api_url_paths()
        print("✓ getApiUrl tests passed")
        sys.exit(0)
    except AssertionError:
        print("✗ getApiUrl tests failed")
        sys.exit(1)
