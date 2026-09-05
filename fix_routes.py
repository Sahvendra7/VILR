with open('app/api/routes.py', 'r') as f:
    content = f.read()

import re
content = re.sub(
    r'(from fastapi import APIRouter.*?\n)',
    r'\1from app.exception.intelligence import ExceptionInvestigation\nfrom app.domain.models import SecurityReceipt\n',
    content
)

with open('app/api/routes.py', 'w') as f:
    f.write(content)
