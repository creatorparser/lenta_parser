import json
import logging

from scrapy import Request, Spider
from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from scrapy.http.response.html import HtmlResponse
from treq import post
from twisted.internet import defer

logger = logging.getLogger("scrapy.camoufox_client")

SERVICE_URL = "http://localhost:8000/scrape"


class DockerDownloadHandler(HTTP11DownloadHandler):  # Убедись, что имя класса правильное

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("🔗 DockerDownloadHandler initialized")

    def download_request(self, request: Request, spider: Spider) -> defer.Deferred:
        if not request.meta.get("camoufox", True):
            logger.debug(f"🔄 Пропускаю через обычный загрузчик: {request.url}")
            return super().download_request(request, spider)

        logger.debug(f"🤖 Отправляю в Docker сервис: {request.url}")

        payload = {
            "url": request.url,
            "block_images": request.meta.get("block_images", True),
            "wait_for_xpath": request.meta.get("wait_for_xpath"),
            "wait_for_timeout": request.meta.get("wait_for_timeout", 10000),
            "get_cookies": request.meta.get("get_camoufox_cookies", False),
            "get_headers": request.meta.get("get_camoufox_headers", False),
        }

        if proxy := request.meta.get('proxy_camoufox'):
            payload["proxy"] = proxy

        d = post(
            SERVICE_URL,
            json=payload,
            timeout=self._get_timeout(request, spider)
        )

        d.addCallback(self._treq_to_text)
        d.addCallback(self._parse_response_text, request)
        d.addErrback(self._on_error, request)

        return d

    def _get_timeout(self, request, spider):
        return request.meta.get("download_timeout", 180)

    def _treq_to_text(self, response):
        return response.text()

    @defer.inlineCallbacks
    def download_request(self, request: Request, spider: Spider):
        if not request.meta.get("camoufox", True):
            defer.returnValue(super().download_request(request, spider))

        logger.debug(f"🤖 Отправляю в Docker сервис: {request.url}")

        payload = {
            "url": request.url,
            "block_images": request.meta.get("block_images", True),
            "wait_for_xpath": request.meta.get("wait_for_xpath"),
            "wait_for_timeout": request.meta.get("wait_for_timeout", 10000),
            "get_cookies": request.meta.get("get_camoufox_cookies", False),
            "get_headers": request.meta.get("get_camoufox_headers", False),
        }

        if proxy := request.meta.get('proxy_camoufox'):
            payload["proxy"] = proxy

        try:
            response = yield post(
                SERVICE_URL,
                json=payload,
                timeout=self._get_timeout(request, spider)
            )
            body_text = yield response.text()

            # body_text - это обычная строка JSON
            # Вызываем парсер и возвращаем результат в Scrapy
            result = self._parse_response_text(body_text, request)
            defer.returnValue(result)

        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
            # Возвращаем ошибку, чтобы Scrapy знал о провале
            raise

    def _parse_response_text(self, body_text: str, request: Request):
        """
        Парсим строку JSON и создаем HtmlResponse.
        """
        try:
            data = json.loads(body_text)
            html_content = data.get("html", "")

            if data.get("cookies"):
                request.meta["camoufox_cookies"] = data["cookies"]

            if data.get("headers"):
                request.meta["camoufox_headers"] = data["headers"]

            return HtmlResponse(
                url=request.url,
                status=200,
                body=html_content.encode('utf-8'),
                request=request,
                encoding='utf-8'
            )
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            logger.error(f"🔎 Тело ответа: {body_text[:500]}...")
            raise ValueError(f"Invalid JSON response: {e}")

    def _on_error(self, failure, request):
        """Этот метод больше не нужен в основной цепочке, если мы используем try/except в inlineCallbacks"""
        logger.error(f"❌ Failure: {failure.getErrorMessage()}")
        return failure