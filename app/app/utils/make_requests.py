import logging
import time

import httpx

logger = logging.getLogger(__name__)

async def make_request(
    method: str,
    url: str,
    logging: bool = False,
    logging_tracker_id: str | int | None = None,
    logging_user_id: int | None = None,
    # request_log_type: RequestLogType = RequestLogType.Outgoing,
    timeout: bool = 60,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    **kwargs,
) -> httpx.Response:
    timeout = httpx.Timeout(timeout)

    async with httpx.AsyncClient(timeout=timeout) as client:
        request = client.build_request(method, url, **kwargs)
        start_time = time.time()
        response = None

        try:
            response = await client.send(request, auth=auth)
            return response

        except httpx.RequestError as e:
            logger.error(f"request error calling external services: details: {str(type(e)) = } {str(e)}")
            response = f"{str(type(e)) = }, {e = }"
            raise e
        except Exception as e:
            logger.error(f"request error calling external services: details: {str(type(e)) = } {str(e)}")
            response = f"{str(type(e)) = }, {e = }"
            raise e
