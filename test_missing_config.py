"""A missing --config file must fail loudly instead of being ignored."""

import subprocess
import sys
from pathlib import Path


def test_missing_config_file_fails(tmp_path):
    script = Path(__file__).parent / "fqcn-fixer.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "-c",
            str(tmp_path / "does-not-exist.yml"),
            "-f",
            "example.yml",
            "-x",
        ],
        cwd=script.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "does-not-exist.yml" in proc.stderr
