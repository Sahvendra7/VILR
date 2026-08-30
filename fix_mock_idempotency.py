with open("tests/integration/test_gateway.py", "r") as f:
    content = f.read()

# I need to find the `gateway` fixture and add behavior for the new idempotency method
fixture_code = """
@pytest.fixture
def gateway(mock_verifier, mock_idempotency, mock_semantic, mock_policy, mock_executor, mock_audit, monkeypatch):
    monkeypatch.setattr('app.domain.gateway.compute_checkout_hash', lambda x: 'ch_123')
"""
new_fixture_code = """
@pytest.fixture
def gateway(mock_verifier, mock_idempotency, mock_semantic, mock_policy, mock_executor, mock_audit, monkeypatch):
    monkeypatch.setattr('app.domain.gateway.compute_checkout_hash', lambda x: 'ch_123')
    
    # Store tokens in a local dict for the mock to use
    fake_tokens = {}
    async def create_token(token, tx_id, auth_data, ttl):
        fake_tokens[token] = {"transaction_id": tx_id, "auth_data": auth_data, "status": "available"}
        
    async def consume_token(token, tx_id):
        if token not in fake_tokens: raise ValueError("Invalid or expired execution token")
        if fake_tokens[token]["transaction_id"] != tx_id:
            from app.domain.errors import InvalidRequest
            raise InvalidRequest("Token transaction mismatch")
        if fake_tokens[token]["status"] == "consumed":
            from app.domain.errors import DuplicateExecution
            raise DuplicateExecution("Execution token already consumed")
        fake_tokens[token]["status"] = "consumed"
        return fake_tokens[token]["auth_data"]
        
    mock_idempotency.create_execution_token.side_effect = create_token
    mock_idempotency.consume_execution_token.side_effect = consume_token
"""
content = content.replace(fixture_code.strip('\n'), new_fixture_code.strip('\n'))

with open("tests/integration/test_gateway.py", "w") as f:
    f.write(content)
