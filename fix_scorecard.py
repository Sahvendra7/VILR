with open("docs/final-security-scorecard.md", "r") as f:
    text = f.read()

import re
old_results = """## 3. Observed Attack Results
From the 186 adversarial benchmark scenarios:
- **BLOCKED**: 180
- **DETECTED**: 6
- **NOT_BLOCKED**: 0
- **ERROR**: 0
- **INCONCLUSIVE**: 0"""

new_results = """## 3. Observed Attack Results
From the 40 adversarial benchmark scenarios in Phase 8:
- **BLOCKED**: 16
- **DETECTED**: 1
- **NOT_BLOCKED**: 23 (Probabilistic LLM attacks and concurrency edge cases, subsequently remediated in Phase 8.5)
- **ERROR**: 0
- **INCONCLUSIVE**: 0"""

text = text.replace(old_results, new_results)

# Also fix the duplicate execution rate line
text = text.replace("Exactly-once external payments rely on provider-side idempotency keys.", "Provider-side exactly-once external payment semantics rely on provider-side idempotency keys.")

with open("docs/final-security-scorecard.md", "w") as f:
    f.write(text)
