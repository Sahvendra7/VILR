import re
with open("tests/integration/test_gemini_provider.py", "r") as f:
    text = f.read()

correct_intent = 'intent = UserIntent(user_id=Identifier("u1"), raw_prompt="I want to buy a high-performance coding laptop", semantic_intent="buy laptop", hard_constraints={"max_budget": "3000.00", "currency": "USD"}, soft_preferences={})'
text = text.replace('intent = UserIntent(user_id=Identifier("u1"), raw_prompt="I want to buy a high-performance coding laptop")', correct_intent)

correct_cart1 = 'CartItem(item_id="dell-xps", name="Dell XPS 15 - 32GB RAM, 1TB SSD", unit_price="2000.00", quantity=1, currency="USD", category="electronics")'
text = text.replace('CartItem(item_id="dell-xps", name="Dell XPS 15 - 32GB RAM, 1TB SSD", unit_price="2000.00")', correct_cart1)

correct_cart2 = 'CartItem(item_id="ps5", name="Sony PlayStation 5 Console", unit_price="500.00", quantity=1, currency="USD", category="electronics")'
text = text.replace('CartItem(item_id="ps5", name="Sony PlayStation 5 Console", unit_price="500.00")', correct_cart2)

with open("tests/integration/test_gemini_provider.py", "w") as f:
    f.write(text)
