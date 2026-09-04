with open("generate_perf.py", "r") as f:
    text = f.read()

text = text.replace('from app.domain.gateway import GatewayAuthorizeRequest\nfrom app.domain.state_machine import TransactionState(', 'from app.domain.gateway import GatewayAuthorizeRequest\nfrom app.domain.state_machine import TransactionState')
text = text.replace('await gateway._log(payload["transaction_id"], "BENCHMARK")', 'await gateway._log(payload["transaction_id"], TransactionState.INTENT_RECEIVED)')
# Actually I messed up the first sed. Let's just overwrite generate_perf.py entirely to be safe!
