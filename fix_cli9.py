with open("demo_template.txt", "r") as f:
    text = f.read()

import re

# Add the lifespan context wrapper correctly
text = text.replace("    if args.llm == \"mock\":\n        from app.semantic.provider", "    async with app.router.lifespan_context(app):\n        if args.llm == \"mock\":\n            from app.semantic.provider")
# Now indent everything after that until the end!
# Actually, wait. It's easier to just construct the whole run_demo correctly.
