#!/usr/bin/env python3
"""Static smoke checks for Rithan AI marketing and manual signup pages."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "site/whatsapp-ai/index.html"
SIGNUP = ROOT / "site/whatsapp-ai/signup/index.html"
V4_CSS = ROOT / "site/whatsapp-ai/v4-orbion.css"
HOME = ROOT / "site/index.html"


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.scripts = []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if props.get("id"):
            self.ids.append(props["id"])
        if tag == "a" and props.get("href"):
            self.links.append(props["href"])
        if tag == "script" and not props.get("src"):
            self.scripts.append("")
            self.in_script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False

    def handle_data(self, data):
        if self.in_script:
            self.scripts[-1] += data


landing = LANDING.read_text()
signup = SIGNUP.read_text()
css = V4_CSS.read_text()
home = HOME.read_text()
doc = Document()
doc.feed(landing)
sign_doc = Document()
sign_doc.feed(signup)

assert len(doc.ids) == len(set(doc.ids)), "Duplicate IDs on landing page"
for expected_id in (
    "product-tab-inbox", "product-tab-agents", "product-tab-flows",
    "product-panel-inbox", "product-panel-agents", "product-panel-flows",
    "features", "why-rithan", "demo", "how", "plans", "faq", "contact"
):
    assert expected_id in doc.ids, f"Missing marketing section: {expected_id}"

for price in ("₹999", "₹2,398", "₹4,196", "₹5,994"):
    assert landing.count(price) == 1, f"Incorrect pricing cards: {price}"
    assert price in home, f"Missing revised price on company homepage: {price}"

assert "₹2,999" not in landing + home, "Outdated WhatsApp AI price"
assert "Instagram" not in landing + signup, "Product page should be WhatsApp-only"
assert "v4-orbion.css" in landing
assert css.count("{") == css.count("}"), "CSS braces do not balance"
assert "https://ai.rithantechnologies.com/" in doc.links, "Sign-in link missing"
assert "https://ai.rithantechnologies.com/signup" in doc.links, "Secure sign-up link missing"
assert "https://ai.rithantechnologies.com/signup" in home, "Homepage sign-up CTA missing"
assert 'http-equiv="refresh"' in signup, "Legacy signup must redirect to the app"
assert "https://ai.rithantechnologies.com/signup" in signup, "Redirect target missing"
assert "https://ai.rithantechnologies.com/signup" in sign_doc.links, "Redirect fallback missing"
for snippet in doc.scripts:
    proc = subprocess.run(
        ["node", "--check"], input=snippet, text=True, capture_output=True, check=False
    )
    assert proc.returncode == 0, f"Invalid landing JS: {proc.stderr}"

print("PASS: marketing, four prices, live sign-in, secure signup and redirect")
