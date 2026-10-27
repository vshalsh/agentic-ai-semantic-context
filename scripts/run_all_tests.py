"""Run each standalone lab in a separate process so imports never collide."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LABS = [
    "001-delegated-authority",
    "002-governed-tools",
    "003-independent-oversight",
    "004-semantic-context",
]

def main():
    for name in LABS:
        directory = ROOT / "examples" / name
        print(f"\\n=== {name} ===", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-p", "test_*.py", "-v"],
            cwd=directory, check=False,
        )
        if result.returncode:
            print(f"FAILED: {name}", file=sys.stderr)
            return result.returncode
    print("All four lab test suites passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
