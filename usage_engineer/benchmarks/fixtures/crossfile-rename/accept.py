import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    # CRLF and LF checkouts of the same file must hash the same
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def main():
    problems = []
    cwd = os.getcwd()

    with open(os.path.join(HERE, "checksums.json"), "r", encoding="utf-8") as f:
        locked = json.load(f)
    test_path = os.path.join(cwd, "tests", "test_behavior.py")
    if not os.path.exists(test_path):
        problems.append("tests/test_behavior.py is missing")
    elif sha256(test_path) != locked["tests/test_behavior.py"]:
        problems.append("tests/test_behavior.py was modified (tests are the acceptance floor)")

    src_dir = os.path.join(cwd, "src")
    if not os.path.isdir(src_dir):
        problems.append("src/ missing")
    else:
        joined = {}
        for name in os.listdir(src_dir):
            if name.endswith(".py"):
                with open(os.path.join(src_dir, name), "r", encoding="utf-8", errors="replace") as f:
                    joined[name] = f.read()
        for name, text in joined.items():
            if "MAX_RETRIES" in text:
                problems.append(f"old name MAX_RETRIES still present in src/{name}")
        for required in ("config.py", "client.py", "worker.py", "__init__.py"):
            if "RETRY_LIMIT" not in joined.get(required, ""):
                problems.append(f"RETRY_LIMIT not found in src/{required}")

    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                       capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        problems.append("unittest discover failed:\n" + (r.stderr or r.stdout)[-1500:])

    if problems:
        print("ACCEPT FAILED:")
        for p in problems:
            print(" -", p)
        return 1
    print("ACCEPT PASSED: constant renamed across the package; behavior tests green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
