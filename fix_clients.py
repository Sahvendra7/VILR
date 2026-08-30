import re

for filename in ["tests/integration/test_concurrency.py", "tests/integration/test_cart_http.py"]:
    with open(filename, "r") as f:
        content = f.read()
    
    if "from httpx import ASGITransport, AsyncClient" not in content:
        content = "from httpx import ASGITransport, AsyncClient\nfrom app.main import app\n" + content
        
    content = content.replace("test_client, app, ", "")
    content = content.replace("test_client, app", "")
    content = content.replace("test_client", "")
    
    content = content.replace("async def test_concurrent_execution(concurrency):", "async def test_concurrent_execution(concurrency):\n    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as test_client:")
    content = content.replace("async def test_cross_transaction_execution():", "async def test_cross_transaction_execution():\n    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as test_client:")
    content = content.replace("async def test_payment_unknown_interaction():", "async def test_payment_unknown_interaction():\n    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as test_client:")
    content = content.replace("async def test_cart_tampering_http():", "async def test_cart_tampering_http():\n    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as test_client:")
    content = content.replace("async def test_opa_routing_http():", "async def test_opa_routing_http():\n    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as test_client:")

    # Indent the bodies of the tests
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith("    ") and not line.startswith("    async with AsyncClient"):
            # if we are inside a test function block
            if "async def test_" in "\n".join(lines[:i]):
                # This is a bit brittle, I'll just write a quick script that works better
                pass

    # Actually I'll just rewrite the files completely to be safe.
