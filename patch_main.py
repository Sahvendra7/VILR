import re
with open('app/main.py', 'r') as f:
    content = f.read()

from_import = "from app.domain.gateway import GatewayOrchestrator"
new_import = "from app.domain.gateway import GatewayOrchestrator\nfrom app.exception.intelligence import ExceptionIntelligenceLayer"

content = content.replace(from_import, new_import)

gateway_init = """    exception_intelligence = ExceptionIntelligenceLayer(semantic_provider)

    app.state.gateway = GatewayOrchestrator(
        verifier=verifier,
        idempotency=idempotency,
        semantic=semantic,
        policy=policy,
        payment_executor=executor,
        audit=audit,
        exception_intelligence=exception_intelligence
    )"""

content = re.sub(
    r"    app.state.gateway = GatewayOrchestrator\(.*?audit=audit\n    \)",
    gateway_init,
    content,
    flags=re.DOTALL
)

with open('app/main.py', 'w') as f:
    f.write(content)

