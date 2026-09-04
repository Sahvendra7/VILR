import re
with open("tests/unit/test_gemini_provider.py", "r") as f:
    text = f.read()

correct_intent = 'intent = UserIntent(user_id=Identifier("u1"), raw_prompt="buy laptop", semantic_intent="buy", hard_constraints={"max_budget": "1000.00", "currency": "USD"}, soft_preferences={})'
text = text.replace('intent = UserIntent(user_id=Identifier("u1"), raw_prompt="buy laptop", semantic_intent="buy", hard_constraints={}, soft_preferences={})', correct_intent)

with open("tests/unit/test_gemini_provider.py", "w") as f:
    f.write(text)
