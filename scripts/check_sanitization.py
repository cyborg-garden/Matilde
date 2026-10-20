"""Local launcher for the canonical sanitization gate. NOT a copy of the gate.

The gate lives in ONE place: cyborg-garden/swarm-map, scripts/check_sanitization.py.
CI runs it through that repo's reusable workflow (.github/workflows/sanitization.yml
here pins it). This launcher fetches the script at the SAME tag and runs it against
this checkout, so `python scripts/check_sanitization.py ...` keeps working locally
and in docs. Every argument is passed through; see the canonical script for modes.

Do not paste the gate in here. Per-repo copies drifted apart, each one quietly
missing a protection another had. To change the gate, change it in swarm-map,
tag it, and bump GATE_TAG here and the `uses: ...@` pin in the workflow together
(tests/test_sanitization_pin.py fails if they disagree).

Offline or testing an unreleased gate: SANITIZE_GATE_PATH=/path/to/check_sanitization.py
"""
import os
import runpy
import sys
import urllib.request

GATE_TAG = "sanitization-gate-v1.0.0"
GATE_URL = ("https://raw.githubusercontent.com/cyborg-garden/swarm-map/"
            f"{GATE_TAG}/scripts/check_sanitization.py")


def gate_path():
    override = os.environ.get("SANITIZE_GATE_PATH", "").strip()
    if override:
        return override
    cache = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
                         "sanitization-gate", GATE_TAG, "check_sanitization.py")
    if not os.path.isfile(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        req = urllib.request.Request(GATE_URL, headers={"User-Agent": "sanitization-gate-launcher/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
        except OSError as exc:
            sys.exit(f"ERROR: could not fetch the sanitization gate {GATE_TAG} ({exc}). "
                     f"Failing closed. Offline? Set SANITIZE_GATE_PATH to a local copy of "
                     f"swarm-map's scripts/check_sanitization.py.")
        tmp = cache + ".part"
        with open(tmp, "wb") as fh:
            fh.write(body)
        os.replace(tmp, cache)
    return cache


if __name__ == "__main__":
    path = gate_path()
    sys.argv = [path] + sys.argv[1:]
    runpy.run_path(path, run_name="__main__")
