import re

with open("docs/technical-deep-dive.md", "r") as f:
    text = f.read()
text = text.replace("localized immutable ledger", "tamper-evident audit chain")
with open("docs/technical-deep-dive.md", "w") as f:
    f.write(text)

with open("docs/final-presentation-script.md", "r") as f:
    text = f.read()
text = text.replace("immutable hash chain", "tamper-evident hash chain")
with open("docs/final-presentation-script.md", "w") as f:
    f.write(text)

with open("docs/test-strategy.md", "r") as f:
    text = f.read()
text = text.replace("| 100% |", "| PASS |")
with open("docs/test-strategy.md", "w") as f:
    f.write(text)
