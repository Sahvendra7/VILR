import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

# Add imports
imports = """
import time
from app.domain.performance import PerformanceTracker
from app.security.risk import DeterministicRiskCalculator
"""
content = content.replace("from datetime import datetime", "from datetime import datetime\n" + imports)

# We will just rewrite authorize completely
import_idx = content.find("class GatewayOrchestrator:")

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
