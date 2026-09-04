with open("demo_template.txt", "r") as f:
    text = f.read()

import re

# Remove the manual hashing imports since generate_valid_payload handles it!
text = re.sub(r'            from app\.security\.crypto import compute_checkout_hash.*?(?=            def safe_generate)', '', text, flags=re.DOTALL)

with open("demo_template.txt", "w") as f:
    f.write(text)

