import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    # CRLF and LF checkouts of the same file must hash the same
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def run_tests():
    return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                          capture_output=True, text=True, cwd=os.getcwd())


def main():
    problems = []
    cwd = os.getcwd()
    src = os.path.join(cwd, "src", "report.py")

    with open(os.path.join(HERE, "checksums.json"), "r", encoding="utf-8") as f:
        locked = json.load(f)
    if not os.path.exists(src):
        problems.append("src/report.py is missing")
    elif sha256(src) != locked["src/report.py"]:
        problems.append("src/report.py was modified (task says do not change source)")

    r1 = run_tests()
    if r1.returncode != 0:
        problems.append("suite does not pass on fixed source:\n" + (r1.stderr or r1.stdout)[-1200:])

    # Prove the new regression test actually catches the old bug:
    if os.path.exists(src):
        backup = src + ".ue-backup"
        shutil.copy2(src, backup)
        try:
            shutil.copy2(os.path.join(HERE, "buggy", "report.py"), src)
            r2 = run_tests()
        finally:
            shutil.copy2(backup, src)
            os.remove(backup)
        if r2.returncode == 0:
            problems.append("suite still passes with the old buggy source: no regression test catches it")

    if problems:
        print("ACCEPT FAILED:")
        for p in problems:
            print(" -", p)
        return 1
    print("ACCEPT PASSED: regression test fails on old buggy source and passes on fixed source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
