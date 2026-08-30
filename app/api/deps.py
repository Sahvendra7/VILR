from fastapi import Request

async def get_gateway(request: Request):
    return request.app.state.gateway
