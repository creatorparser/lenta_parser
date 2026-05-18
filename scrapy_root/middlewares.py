import json
import logging
from typing import Tuple

from scrapy import signals
from scrapy.exceptions import IgnoreRequest

logger = logging.getLogger(__name__)


class CookieProxyRetryMiddleware:
    """Middleware для автоматической обработки 403 ошибок через смену кук и прокси"""

    def __init__(self, database_service):
        self.max_retries = 3
        self.database_service = database_service

    @classmethod
    def from_crawler(cls, crawler):
        # Получаем DatabaseService из crawler
        database_service = crawler.spider.database_service

        middleware = cls(database_service)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        logger.info(f'CookieProxyRetryMiddleware активирован для {spider.name}')

    def _get_retry_count(self, request):
        """Получает текущее количество попыток из meta запроса"""
        return request.meta.get('cookie_retry_count', 0)

    def _should_retry(self, request):
        """Проверяет, нужно ли делать повторную попытку"""
        return self._get_retry_count(request) < self.max_retries

    def get_cookies(self, store_id: int) -> Tuple[str, str, str]:
        """Получение cookies и прокси для указанного магазина"""
        try:
            query = f"""SELECT cookies, proxy, headers FROM cookies_headers
                      WHERE store_id = {store_id}
                      ORDER BY RANDOM() LIMIT 1 FOR UPDATE SKIP LOCKED"""

            result = self.database_service.execute_query(query)

            if not result:
                raise ValueError(f"Нет доступных cookies для store_id {store_id}")

            cookies, proxy, headers = result[0]
            logger.info(f"Получены данные из БД для store_id {store_id}:")
            logger.info(f"  Proxy: {proxy}")
            logger.info(f"  Cookies (первые 100 символов): {cookies[:100] if cookies else 'None'}...")
            logger.info(f"  Headers (первые 100 символов): {headers[:100] if headers else 'None'}...")

            return cookies, proxy, headers

        except Exception as e:
            logger.error(f"Ошибка при получении cookies для store_id {store_id}: {e}")
            raise

    def delete_cookie(self, store_id: int, proxy: str) -> bool:
        """Удаление cookies для указанного магазина и прокси"""
        try:
            query = """DELETE FROM cookies_headers 
                      WHERE store_id = %s AND proxy = %s"""

            affected_rows = self.database_service.execute_update(query, (store_id, proxy))

            if affected_rows > 0:
                logger.info(f"Удалены cookies для store_id {store_id} и прокси {proxy}")
                return True
            else:
                logger.warning(f"Cookies для store_id {store_id} и прокси {proxy} не найдены")
                return False

        except Exception as e:
            logger.error(f"Ошибка при удалении cookies для store_id {store_id}: {e}")
            return False

    def _update_request_with_new_credentials(self, request, store_id, spider):
        """Обновляет запрос новыми куками и прокси"""
        try:
            # Получаем новые credentials
            cookies, proxy, headers = self.get_cookies(store_id)

            logger.info(f"Установка credentials для {request.url}:")
            logger.info(f"  Proxy из БД: {proxy}")

            # Парсим cookies
            try:
                parsed_cookies = json.loads(cookies)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга cookies: {e}")
                logger.error(f"  Cookies строка: {cookies}")
                raise

            # Устанавливаем в запрос
            request.cookies = parsed_cookies
            proxy = proxy.replace('\n', '')
            request.meta['proxy'] = proxy

            # Сохраняем для последующего удаления
            request.meta['used_cookies'] = cookies
            request.meta['used_proxy'] = proxy
            request.meta['cookie_retry_count'] = self._get_retry_count(request) + 1

            spider.logger.info(
                f'Используем новые credentials для store_id={store_id}. '
                f'Proxy: {proxy}, Попытка: {request.meta["cookie_retry_count"]}\n {request.url}'
            )
            return True

        except Exception as e:
            spider.logger.error(f'Ошибка при получении новых credentials: {str(e)}')
            return False

    def process_request(self, request, spider):
        """Устанавливает куки и прокси при первом запросе"""
        logger.info(f"process_request для {request.url}")
        logger.info(f"  used_cookies в meta: {'used_cookies' in request.meta}")

        # Устанавливаем credentials только если их еще нет
        if 'used_cookies' not in request.meta:
            logger.info(f"  Устанавливаем начальные credentials")
            if not self._update_request_with_new_credentials(request, spider.store_id, spider):
                raise IgnoreRequest("Не удалось установить начальные credentials")
        else:
            logger.info(f"  Credentials уже установлены, пропускаем")

    def process_response(self, request, response, spider):
        logger.info(f"process_response для {request.url}")
        logger.info(f"  Status: {response.status}")

        error_text = request.meta.get('error_text')
        if response.status in [403, 401] or (error_text is not None and error_text in response.text):
            current_retry = self._get_retry_count(request)

            spider.logger.warning(
                f'Получен {response.status} ответ для {request.url}. '
                f'Попытка {current_retry + 1} из {self.max_retries}'
            )
            # Удаляем старые credentials
            if 'used_proxy' in request.meta:
                logger.info(f"  Удаляем старые credentials для прокси: {request.meta['used_proxy']}")
                self.delete_cookie(
                    spider.store_id,
                    request.meta['used_proxy']
                )

            # Проверяем возможность повтора
            if not self._should_retry(request):
                spider.logger.error(
                    f'Достигнут лимит повторов ({self.max_retries}) для {request.url}'
                )
                return response

            # Создаем новый запрос с обновленными credentials
            new_request = request.copy()
            logger.info(f'  Старый запрос cookies: {new_request.cookies}')
            logger.info(f'  Старый запрос proxy: {new_request.meta.get("proxy")}')
            if self._update_request_with_new_credentials(new_request, spider.store_id, spider):
                logger.info(f'  Новый запрос cookies: {new_request.cookies}')
                logger.info(f'  Новый запрос proxy: {new_request.meta.get("proxy")}')
                return new_request

            spider.logger.error('Не удалось получить новые credentials для повтора')
        return response
