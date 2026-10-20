"""The sanitization gate is canonical (cyborg-garden/swarm-map); this repo keeps
only its sanitize.config.json, a caller workflow and a local launcher. The one
thing that can drift here is the pin: the workflow's `uses: ...@<tag>` and the
launcher's GATE_TAG must name the same release, or local runs and CI would judge
the same diff with different gates."""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
USES = re.compile(r"uses:\s*cyborg-garden/swarm-map/\.github/workflows/sanitization-gate\.yml@(\S+)")


def _workflow_pins():
    pins = {}
    wf_dir = os.path.join(ROOT, ".github", "workflows")
    for name in sorted(os.listdir(wf_dir)):
        with open(os.path.join(wf_dir, name), encoding="utf-8") as fh:
            for tag in USES.findall(fh.read()):
                pins.setdefault(tag, []).append(name)
    return pins


def _launcher_tag():
    with open(os.path.join(ROOT, "scripts", "check_sanitization.py"), encoding="utf-8") as fh:
        return re.search(r'^GATE_TAG = "([^"]+)"', fh.read(), re.M).group(1)


def test_the_gate_is_called_and_pinned_to_a_release_tag():
    pins = _workflow_pins()
    assert pins, "no workflow calls the canonical sanitization gate"
    for tag in pins:
        assert re.fullmatch(r"sanitization-gate-v\d+\.\d+\.\d+", tag), (
            f"pin the gate to a sanitization-gate-vX.Y.Z tag, not {tag!r}")


def test_launcher_and_workflows_pin_the_same_release():
    assert set(_workflow_pins()) == {_launcher_tag()}


def test_no_vendored_copy_of_the_gate():
    """The launcher must stay a launcher: no detector patterns pasted back in."""
    with open(os.path.join(ROOT, "scripts", "check_sanitization.py"), encoding="utf-8") as fh:
        assert "_DETERMINISTIC_PATTERNS" not in fh.read()


def test_config_is_valid_json_with_sensitive_prefixes():
    with open(os.path.join(ROOT, "sanitize.config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    assert cfg.get("sensitive_prefixes"), "sanitize.config.json must declare sensitive_prefixes"
