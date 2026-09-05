import re

with open('app/api/routes.py', 'r') as f:
    content = f.read()

from_models = "from app.domain.models import UserIntent, Cart, ExecutionReceipt"
new_models = "from app.domain.models import UserIntent, Cart, ExecutionReceipt, SecurityReceipt\nfrom app.exception.intelligence import ExceptionInvestigation"
content = content.replace(from_models, new_models)

new_routes = """
@router.post("/v1/investigate/{transaction_id}", response_model=ExceptionInvestigation)
async def investigate_transaction(
    transaction_id: str,
    gateway=Depends(get_gateway)
):
    try:
        return await gateway.investigate_transaction(transaction_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/v1/receipt/{transaction_id}", response_model=SecurityReceipt)
async def get_receipt(
    transaction_id: str,
    gateway=Depends(get_gateway)
):
    try:
        return await gateway.generate_receipt(transaction_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
"""

content = content + new_routes

with open('app/api/routes.py', 'w') as f:
    f.write(content)
