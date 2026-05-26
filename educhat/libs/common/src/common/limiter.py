from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Initialize limiter with remote address key function
# Default storage is in-memory. For production with multiple workers/instances, 
# you should set storage_uri="redis://..." in Limiter constructor.
limiter = Limiter(key_func=get_remote_address)

def rate_limit_key_func(request: Request):
    """
    Custom key function for rate limiting. 
    Can be extended to use User ID if authenticated, else IP.
    """
    if hasattr(request, "state") and hasattr(request.state, "user"):
        return request.state.user.username
    return get_remote_address(request)
