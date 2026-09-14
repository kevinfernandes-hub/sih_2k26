import asyncio
from backend.main import discover_and_verify, DiscoverAndVerifyRequest

class Req(DiscoverAndVerifyRequest):
    query: str = "MIHAN"
    before_date: str = "2019-01-01"
    after_date: str = "2025-01-01"
    analysis_mode: str = "built-up"

async def test():
    print("Testing discover_and_verify...")
    res = await discover_and_verify(Req())
    print("Success:", res)

asyncio.run(test())
