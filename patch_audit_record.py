with open('app/domain/models.py', 'r') as f:
    content = f.read()

import re
content = re.sub(
    r'    record_hash: str\n',
    '    record_hash: str\n    investigation: Optional[Dict[str, Any]] = None\n',
    content
)

with open('app/domain/models.py', 'w') as f:
    f.write(content)
