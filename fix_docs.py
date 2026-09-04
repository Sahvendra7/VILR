import re

with open("docs/architecture.md", "r") as f:
    text = f.read()

# I will just append a section explaining Semantic Provider Architecture.
semantic_section = """
## 9. Semantic Provider Architecture
VILR implements a strict separation of concerns around AI evaluation. The system currently supports:
1. **Mock semantic provider** (`MockLLMProvider`): The default provider used for deterministic unit and integration testing.
2. **Gemini-backed provider** (`GeminiLLMProvider`): Uses the official `google-genai` Python SDK to perform real semantic evaluation against the Gemini API using structured outputs.

**Security Constraints:**
- The LLM provides *probabilistic semantic evidence* that is independently evaluated by *deterministic policy*.
- Gemini does **not** guarantee security, nor does it deterministically prevent all prompt injections. It is treated exclusively as an untrusted evidence generator.
- AI cannot authorize money movement. The OPA engine is strictly responsible for interpreting the semantic evaluation's `status` and rendering a deterministic authorization decision.
"""
text = text + semantic_section
with open("docs/architecture.md", "w") as f:
    f.write(text)
