import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORBIDDEN_IN_CART = ("margin-left", "padding-left", "text-align: left", "left:")


def rule_block(css, selector):
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return m.group(1) if m else None


def main():
    problems = []
    cwd = os.getcwd()
    html_path = os.path.join(cwd, "index.html")
    css_path = os.path.join(cwd, "styles.css")
    for p in (html_path, css_path):
        if not os.path.exists(p):
            problems.append(f"missing {os.path.basename(p)}")
    if problems:
        print("ACCEPT FAILED:")
        for p in problems:
            print(" -", p)
        return 1

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    if not re.search(r"<html[^>]*\bdir=\"rtl\"", html):
        problems.append('document is not RTL: missing dir="rtl" on <html>')
    if 'lang="he"' not in html:
        problems.append('missing lang="he" on <html>')

    block = rule_block(css, ".cart")
    if block is None:
        problems.append(".cart rule not found in styles.css")
    else:
        if not re.search(r"direction\s*:\s*rtl", block):
            problems.append(".cart must set direction: rtl")
        if not re.search(r"text-align\s*:\s*right", block):
            problems.append(".cart must set text-align: right")
        if not re.search(r"margin-inline-start\s*:", block):
            problems.append(".cart must use margin-inline-start instead of a left-only margin")
        for bad in FORBIDDEN_IN_CART:
            if bad in block:
                problems.append(f".cart still contains left-only rule: {bad!r}")

    price = rule_block(css, ".price")
    if price is None or not re.search(r"direction\s*:\s*ltr", price):
        problems.append(".price (numbers/currency) must keep direction: ltr with bidi isolation")

    if problems:
        print("ACCEPT FAILED:")
        for p in problems:
            print(" -", p)
        return 1
    print("ACCEPT PASSED: RTL direction applied to the cart while prices stay LTR-safe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
