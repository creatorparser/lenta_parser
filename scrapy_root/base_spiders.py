import json
import logging
import random
import time
from typing import Dict, Any

import redis
from scrapy import signals
from scrapy.spiders import Spider

from scrapy_root.services.database_service import DatabaseService
from scrapy_root.utils.funcs import get_all_str


logger = logging.getLogger(__name__)


class CrawlerSpider(Spider):
    name = None
    store_id = 0

    def __init__(self, name_spider, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer = None
        self.item_processed = None
        self.list_links = None
        self.name_queue = kwargs['name_queue']

        self._init_services(kwargs)

        # Получаем путь к файлу прокси из параметров или используем дефолтный
        proxy_file = kwargs.get('proxy_file', 'files/list_proxies.txt')
        logger.info(f"Используется файл прокси: {proxy_file}")
        self.user_agents = get_all_str('files/useragents.txt')
        self.list_proxies = get_all_str(proxy_file)
        self.COUNT_ERROR = 0
        self.MAX_ERRORS = 50

    def _init_services(self, kwargs: Dict[str, Any]):
        """Инициализация сервисов"""
        try:
            # Инициализация сервиса базы данных
            self.database_service = DatabaseService(
                hostname=kwargs.get('hostname'),
                username=kwargs.get('username'),
                password=kwargs.get('password'),
                database=kwargs.get('database'),
                port=kwargs.get('port')
            )

            self.redis_connection = redis.StrictRedis(
                host='localhost',
                port=kwargs.get('port_redis'),
                # charset='utf-8',
                decode_responses=True
            )

            logger.info("Сервисы успешно инициализированы")

        except Exception as e:
            logger.error(f"Ошибка при инициализации сервисов: {e}")
            raise

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # Извлекаем proxy_file из kwargs, чтобы избежать дублирования
        proxy_file = kwargs.pop('proxy_file', None)
        
        # Формируем параметры для передачи в родительский класс
        spider_kwargs = {
            'hostname': crawler.settings.get("HOSTNAME_POSTGRESQL"),
            'username': crawler.settings.get("USERNAME_POSTGRESQL"),
            'password': crawler.settings.get("PASSWORD_POSTGRESQL"),
            'database': crawler.settings.get("DATABASE_POSTGRESQL"),
            'port': crawler.settings.get("PORT_POSTGRESQL"),
            'port_redis': crawler.settings.get("PORT_REDIS"),
            'crawler': crawler,
            'proxy': kwargs.get('PROXY'),
            'name_queue': kwargs.get('NAME_QUEUE'),
        }
        
        # Добавляем proxy_file только если он был передан
        if proxy_file is not None:
            spider_kwargs['proxy_file'] = proxy_file
        
        spider = super().from_crawler(
        # spider = cls(
            *args,
            **spider_kwargs,
            **kwargs
        )
        # return spider
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)

        return spider

    def spider_closed(self, spider, reason):
        """Обработчик закрытия spider"""
        try:
            spider_stats = self.crawler.stats.get_stats()
            logger.info(f'Spider {self.name} закрыт с причиной: {reason}')
            logger.debug(f'Статистика spider: {spider_stats}')
        except Exception as e:
            logger.error(f"Ошибка при закрытии spider: {e}")
        finally:
            # Очистка ресурсов
            self._cleanup()

    def _cleanup(self):
        """Очистка ресурсов"""
        try:
            if hasattr(self, 'database_service'):
                self.database_service.close()

            if hasattr(self, 'redis_connection'):
                self.redis_connection.close()

            logger.info("Ресурсы успешно очищены")

        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов: {e}")

    def create_queue(self, name_spider):
        if not self.redis_connection.exists(name_spider):
            self.crawler.engine.close_spider(self, 'No elements in redis')
        self.redis_connection.delete(f'{name_spider}_queue')
        set_members = self.redis_connection.smembers(name_spider)
        self.redis_connection.rpush(f'{name_spider}_queue', *set_members)

    def get_redis_data(self, name_spider):
        list_length = self.redis_connection.llen(f'{name_spider}_queue')
        if list_length == 0:
            return
        random_index = random.randint(0, list_length - 1)
        dict_url = self.redis_connection.lindex(f'{name_spider}_queue', random_index)
        self.redis_connection.lrem(f'{name_spider}_queue', 1, dict_url)
        try:
            return_data = json.loads(dict_url)
        except json.decoder.JSONDecodeError or KeyError:
            return_data = dict_url
        return return_data

    def attr_meta(self, **kwargs):
        meta = {
            # 'impersonate': self.crawler.settings.get('IMPERSONATE'),
            'proxy': self.proxy,
            'proxy_camoufox': self.proxy,
            'start_time': time.time(),
            'repeats': 0,
            'position_product': 0,
            'headless': False
        }
        meta.update(kwargs)
        return meta

    def get_random_user_agent(self):
        """Читает случайный user-agent из файла useragents.txt"""
        with open('files/useragents.txt', 'r', encoding='utf-8') as f:
            user_agents = [line.strip() for line in f if line.strip()]
        if user_agents:
            return random.choice(user_agents)
