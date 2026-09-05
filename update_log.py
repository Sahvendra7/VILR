import re

with open('app/domain/gateway.py', 'r') as f:
    content = f.read()

content = content.replace(
    '"prev_record_hash": prev_hash',
    '"prev_record_hash": prev_hash,\n            "investigation": kwargs.get("investigation")'
)

with open('app/domain/gateway.py', 'w') as f:
    f.write(content)
