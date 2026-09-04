import re
with open("app/api/routes.py", "r") as f:
    content = f.read()

# Remove /intents
content = re.sub(r'@router.post\("/intents".*?return IntentResponse\(status="SUCCESS", message="Intent normalized successfully"\)', '', content, flags=re.DOTALL)

# Remove /verify
content = re.sub(r'@router.post\("/verify".*?return VerifyResponse\(transaction_id=req.transaction_id, status="SUCCESS", isValid=True\)', '', content, flags=re.DOTALL)

with open("app/api/routes.py", "w") as f:
    f.write(content)
