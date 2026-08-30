with open("tests/integration/test_gateway.py", "r") as f:
    content = f.read()

# Add a mock for compute_checkout_hash inside the test module
if "@pytest.fixture\ndef gateway" in content:
    content = content.replace(
        "def gateway(mock_verifier, mock_idempotency, mock_semantic, mock_payment, mock_audit, mock_policy):",
        "def gateway(mock_verifier, mock_idempotency, mock_semantic, mock_payment, mock_audit, mock_policy, mocker):\n    mocker.patch('app.domain.gateway.compute_checkout_hash', return_value='ch_123')"
    )

with open("tests/integration/test_gateway.py", "w") as f:
    f.write(content)
