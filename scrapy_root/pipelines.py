import json
import logging
import time
from datetime import datetime, timezone

from scrapy_root.services.database_service import DatabaseService
from .utils.funcs import get_value

logger = logging.getLogger(__name__)

class BasePipeline:

    def __init__(self, crawler):
        self.crawler = crawler
        self._init_services(self)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def _init_services(self, crawler):
        """Инициализация сервисов"""
        try:
            # Инициализация сервиса базы данных
            self.database_service = DatabaseService(
                hostname=self.crawler.settings['HOSTNAME_POSTGRESQL'],
                username=self.crawler.settings['USERNAME_POSTGRESQL'],
                password=self.crawler.settings['PASSWORD_POSTGRESQL'],
                database=self.crawler.settings['DATABASE_POSTGRESQL'],
                port=self.crawler.settings['PORT_POSTGRESQL'],
            )

            logger.info("Сервисы успешно инициализированы")

        except Exception as e:
            logger.error(f"Ошибка при инициализации сервисов: {e}")
            raise


class CatalogPipeline(BasePipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_item(self, item, spider):
        data_items = item['products_data']

        for product in data_items:
            try:
                self.insert_product(product, spider)
            except Exception as e:
                spider.logger.error(f"Error processing product {product}: {e}")
                continue

        spider.logger.warning(f'Вставляем {len(data_items)} элементов')
        return item

    def insert_product(self, product, spider):
        product_data = {
            'title': get_value(product, ['title']),
            'sku': get_value(product, ['sku']),
            'price': get_value(product, ['price']),
            'price_card': get_value(product, ['price_card']),
            'url': get_value(product, ['url']),
            'img_url': get_value(product, ['img_url']),
            'created_at': get_value(product, ['created_at']),
        }
        
        columns = ', '.join(product_data.keys())
        placeholders = ', '.join([f'%({key})s' for key in product_data.keys()])
        insert_query = f"INSERT INTO products ({columns}) VALUES ({placeholders})"
        
        self.database_service.execute_update(insert_query, product_data)


class CookiesHeadersPipeline(BasePipeline):
    def process_item(self, item, spider):
        dict_insert = {
            'url': item['request_url'],
            'time_request': time.time() - item['start_time'],
            'spider': item['spider'],
            'store_id': item['store_id'],
            'meta': json.dumps(item['meta']),
            'cookies': json.dumps(dict(item['cookies'])),
            'headers': json.dumps(dict(item['headers'])),
            'type_proxy': item.get('TYPE_PROXY'),
            'provider_proxy': item.get('PROVIDER_PROXY'),
            'proxy': item['proxy'],
            'date_added': datetime.now(timezone.utc),
        }

        query_insert = """
            INSERT INTO cookies_headers (url, cookies, headers, proxy, store_id, meta, spider, type_proxy, provider_proxy, date_added, time_request)
            VALUES (%(url)s, %(cookies)s, %(headers)s,  %(proxy)s, %(store_id)s, %(meta)s, %(spider)s, %(type_proxy)s, %(provider_proxy)s, %(date_added)s, %(time_request)s)
        """
        logger.info(f"Сохраняем куки для прокси {item['proxy']}")
        self.database_service.execute_update(query_insert, dict_insert)
        return item
