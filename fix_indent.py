import re
for fn in ["tests/integration/test_concurrency.py", "tests/integration/test_cart_http.py"]:
    with open(fn, 'r') as f:
        content = f.read()
    
    # We replaced 'async with AsyncClient' with 'async with app.router.lifespan_context(app):\n        async with AsyncClient'
    # BUT we didn't indent the rest of the function!
    # I will just write a simpler fix.
    
    content = content.replace('async with app.router.lifespan_context(app):\n        async with AsyncClient', 'async with app.router.lifespan_context(app), AsyncClient')
    with open(fn, 'w') as f:
        f.write(content)

