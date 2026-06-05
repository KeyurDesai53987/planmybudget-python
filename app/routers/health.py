from fastapi import APIRouter
import httpx

router = APIRouter()


@router.get("/api/status")
async def status():
    return {"status": "ok"}


@router.get("/api/health")
async def health():
    return {"status": "healthy"}


@router.get("/api/exchange-rates")
async def exchange_rates():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.exchangerate-api.com/v4/latest/USD")
            if resp.status_code == 200:
                data = resp.json()
                return {"rates": data.get("rates", {})}
    except Exception:
        pass
    return {"rates": {}}
