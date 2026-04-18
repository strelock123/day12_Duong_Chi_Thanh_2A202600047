import redis
import time
from fastapi import HTTPException
from app.config import settings

# Initialize Redis client
# Assuming REDIS_URL like 'redis://localhost:6379/0'
r = None
if settings.redis_url:
    r = redis.from_url(settings.redis_url)

def check_rate_limit(user_id: str):
    if not r:
        return # Skip if no redis configured
        
    now = time.time()
    key = f"rate_limit:{user_id}"
    
    # Use Redis as pipeline
    pipe = r.pipeline()
    # Remove old requests
    pipe.zremrangebyscore(key, 0, now - 60)
    # Count requests in window
    pipe.zcard(key)
    # Add new request
    pipe.zadd(key, {str(now): now})
    # Set TTL for the key
    pipe.expire(key, 60)
    
    results = pipe.execute()
    request_count = results[1]
    
    if request_count >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"}
        )
