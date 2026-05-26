import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

def create_async_client(timeout: float = 10.0, retries: int = 3) -> httpx.AsyncClient:
    """
    Creates an httpx.AsyncClient with configured timeout.
    Note: 'tenacity' retry logic is best applied at the call site or via a wrapper, 
    as httpx transport doesn't handle application-level retries natively in the strict sense.
    But we can configure the client transport to be robust.
    """
    transport = httpx.AsyncHTTPTransport(retries=retries)
    return httpx.AsyncClient(timeout=timeout, transport=transport)

# Decorator for easy retry usage
retry_request = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout))
)
