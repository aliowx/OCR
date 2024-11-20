import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create a global client session
global_client = httpx.AsyncClient(
    timeout=httpx.Timeout(60), verify=settings.PAYMENT_REQUEST_VERIFY_SSL
)


async def make_request(
    method: str,
    url: str,
    auth: (
        httpx._types.AuthTypes | httpx._client.UseClientDefault | None
    ) = httpx.USE_CLIENT_DEFAULT,
    client: httpx.AsyncClient = global_client,  # Use the global client by default
    **kwargs,
) -> httpx.Response:
    request = client.build_request(method, url, **kwargs)

    try:
        response = await client.send(request, auth=auth)
        return response

    except httpx.RequestError as e:
        logger.error(
            f"request error calling external services: details: {str(type(e)) = } {str(e)}"
        )
        raise e
    except Exception as e:
        logger.error(
            f"request error calling external services: details: {str(type(e)) = } {str(e)}"
        )
        raise e
