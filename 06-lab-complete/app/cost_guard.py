import redis
from datetime import datetime
from fastapi import HTTPException
from app.config import settings

r = None
if settings.redis_url:
    r = redis.from_url(settings.redis_url)

def check_and_record_cost(user_id: str, input_tokens: int, output_tokens: int) -> bool:
    if not r:
        return True # Skip if no redis configured
        
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    current = float(r.get(key) or 0)
    
    if current + cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail="Monthly budget exceeded."
        )
        
    r.incrbyfloat(key, cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
