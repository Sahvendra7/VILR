import re

with open("docs/architecture.md", "r") as f:
    content = f.read()

state_note = """
### 4.4 Transaction State (Prototype Note)
> [!NOTE]
> The current prototype stores transaction state (e.g., `_tx_states`) in-memory via a simple dictionary. This limits the gateway to a single-process deployment. 
> 
> **Production Evolution Path:** For a highly available, multi-instance production environment, the `_tx_states` dictionary must be replaced by a shared, durable state store (such as Redis or PostgreSQL) to allow different nodes to resume and execute transactions seamlessly.
"""

content = content.replace("## 5. Security & Isolation Properties", state_note + "\n## 5. Security & Isolation Properties")

with open("docs/architecture.md", "w") as f:
    f.write(content)
