import re
with open('README.md', 'r') as f:
    content = f.read()

content += """
## Tier 1 Security Enhancements
- **Exception Intelligence**: Advisory/explanatory only. LLM has no authorization authority.
- **Security Receipt**: Deterministic evidence generated from actual system state.
- **Ground-Truth Evaluation**: Expected decision vs actual decision + expected side effect vs actual side effect.
- **Supabase**: Persistent tamper-evident audit storage.
"""
with open('README.md', 'w') as f:
    f.write(content)
