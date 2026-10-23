import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    # CRLF and LF checkouts of the same file must hash the same
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def main():
    problems = []

    # 1. tests must not be modified (checksum measured against the pristine fixture)
    with open(os.path.join(HERE, "checksums.json"), "r", encoding="utf-8") as f:
        locked = json.load(f)
    test_path = os.path.join(os.getcwd(), "tests", "test_calc.py")
    if not os.path.exists(test_path):
        problems.append("tests/test_calc.py is missing")
    elif sha256(test_path) != locked["tests/test_calc.py"]:
        problems.append("tests/test_calc.py was modified (tests are the acceptance floor)")

    # 2. behavior: exercise the requirement directly, independent of the test file
    sys.path.insert(0, os.getcwd())
    try:
        from src.calc import sum_range
        if sum_range(1, 3) != 6:
            problems.append(f"sum_range(1,3) == {sum_range(1, 3)}, expected 6")
        if sum_range(5, 5) != 5:
            problems.append(f"sum_range(5,5) == {sum_range(5, 5)}, expected 5")
        if sum_range(-2, 2) != 0:
            problems.append(f"sum_range(-2,2) == {sum_range(-2, 2)}, expected 0")
    except Exception as e:
        problems.append(f"import/behavior failed: {type(e).__name__}: {e}")

    # 3. the shipped test suite must pass
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                       capture_output=True, text=True, cwd=os.getcwd())
    if r.returncode != 0:
        problems.append("unittest discover failed:\n" + (r.stderr or r.stdout)[-1500:])

    if problems:
        print("ACCEPT FAILED:")
        for p in problems:
            print(" -", p)
        return 1
    print("ACCEPT PASSED: inclusive-range bug fixed; tests untouched and green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
