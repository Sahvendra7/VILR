for filename in ["tests/integration/test_concurrency.py", "tests/integration/test_cart_http.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # Wrap the body in async with app.router.lifespan_context(app) as state:
    if "app.router.lifespan_context(app)" not in content:
        content = content.replace('async with AsyncClient', 'async with app.router.lifespan_context(app):\n        async with AsyncClient')
    
    with open(filename, "w") as f:
        f.write(content)
