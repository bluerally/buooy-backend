from typing import Callable, Awaitable

from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

from common.config import logger


class LoggingAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            await self._request_log(request)
            response: Response = await original_route_handler(request)
            self._response_log(request, response)  # 수정된 부분
            return response

        return custom_route_handler

    @staticmethod
    def _has_json_body(request: Request) -> bool:
        if (
            request.method in ("POST", "PUT", "PATCH")
            and request.headers.get("content-type") == "application/json"
        ):
            return True
        return False

    async def _request_log(self, request: Request) -> None:
        body = ""
        if self._has_json_body(request):
            request_body = await request.body()
            body = request_body.decode("UTF-8")

        headers = dict(request.headers)

        extra = {
            "httpMethod": request.method,
            "url": request.url.path,
            "headers": str(headers),
            "queryParams": str(request.query_params),
            "body": body,
        }
        logger.info(f"Request Info: {extra}")

    @staticmethod
    def _response_log(request: Request, response: Response) -> None:
        extra = {
            "httpMethod": request.method,
            "url": request.url.path,
            "headers": str(dict(request.headers)),
            "queryParams": str(request.query_params),
            "body": response.body.decode("UTF-8") if response.body else "",
        }
        logger.info(f"Response Info: {extra}")
