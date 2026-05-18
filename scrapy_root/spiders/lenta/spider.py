import json
import os.path
import aiohttp
from datetime import datetime

from scrapy.spiders import Request

from scrapy_root.base_spiders import CrawlerSpider
from scrapy_root.items import CatalogItem, CookiesHeadersItem
from scrapy_root.spiders.lenta.headers import product_headers, generate_sessiontoken
from scrapy_root.utils.funcs import get_value

directory_spider = os.path.dirname(os.path.abspath(__file__))
name_spider = os.path.basename(directory_spider)


class CreateCookies(CrawlerSpider):
    name = f'{name_spider}_cookies'
    store_id = 1
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_root.handlers.docker_handler.DockerDownloadHandler",
            "https": "scrapy_root.handlers.docker_handler.DockerDownloadHandler"
        },
        'ITEM_PIPELINES': {
            'scrapy_root.pipelines.CookiesHeadersPipeline': 200,
        },
        'LOG_FILE': f'files/logs/{name}.log',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(name_spider, *args, **kwargs)
        self.database_service.execute_update(f'DELETE FROM cookies_headers WHERE store_id = {self.store_id};')

    async def start(self):
        for proxy in self.list_proxies:
            yield Request(
                url='https://lenta.com/',
                callback=self.parse,
                dont_filter=True,
                meta=self.attr_meta(
                    camoufox=True,
                    proxy=proxy,
                    proxy_camoufox=proxy,
                    wait_for_xpath='//div[@class="slider-container"]',
                    get_camoufox_cookies=True,
                    get_camoufox_headers=True,
                ),
            )

    async def parse(self, response):
        item = CookiesHeadersItem()
        item['start_time'] = response.request.meta['start_time']
        item['request_url'] = response.url
        item['spider'] = self.name
        item['store_id'] = self.store_id
        item['meta'] = response.meta
        item['cookies'] = response.meta['camoufox_cookies']
        item['headers'] = response.meta['camoufox_headers']
        item['proxy'] = response.meta['proxy_camoufox']
        yield item


class CreateLinks(CrawlerSpider):
    name = f'{name_spider}_links'
    store_id = 1

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_root.handlers.docker_handler.DockerDownloadHandler",
            "https": "scrapy_root.handlers.docker_handler.DockerDownloadHandler"
        },
        'LOG_FILE': f'files/logs/{name}.log',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(name_spider, *args, **kwargs)
        self.redis_connection.delete(name_spider)

    async def start(self):
        yield Request(
            url='https://lenta.com/catalog/',
            callback=self.parse,
            meta=self.attr_meta(
                camoufox=True,
                wait_for_xpath='//div[@class="catalog-mobile-panel-item"]',
            ),
        )

    async def parse(self, response):
        categories = response.xpath('//div[@class="catalog-mobile-panel-item"]//a/@href').getall()
        for category_url in categories:
            category_id = category_url.split('-')[-1]
            category_id = category_id[:-1]
            insert_data = {
                'category_id': category_id,
                'category_name': category_url,
                'page_number': 0,
            }
            insert_data = json.dumps(insert_data)
            self.logger.info(f'Вставляем элемент {insert_data}')
            self.redis_connection.sadd(name_spider, insert_data)


class Catalog(CrawlerSpider):
    name = f'{name_spider}_catalog'
    store_id = 1

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy_root.middlewares.CookieProxyRetryMiddleware': 200,
        },
        'ITEM_PIPELINES': {
            'scrapy_root.pipelines.CatalogPipeline': 200,
        },
        'LOG_FILE': f'files/logs/{name}.log',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(name_spider, *args, **kwargs)
        self.create_queue(name_spider)
        
        # Получаем адрес из параметров
        self.address = kwargs.get('address', None)
        
        # Генерируем и сохраняем sessiontoken
        self.sessiontoken = generate_sessiontoken()
        self.logger.info(f'Сгенерирован sessiontoken: {self.sessiontoken}')
        
        # Флаг для отслеживания выполнения запроса
        self.delivery_mode_set = False

    async def get_stores_list(self):
        """
        Получает список всех магазинов через API Lenta.
        """
        url = 'https://lenta.com/api-gateway/v1/stores/pickup/search'
        json_data = {}
        headers = product_headers(self, self.sessiontoken)
        
        self.logger.info(f'Получаем список магазинов через API: {url}')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=json_data, headers=headers) as response:
                    self.logger.info(f'Статус ответа при получении списка магазинов: {response.status}')
                    if response.status == 200:
                        data = await response.json()
                        stores_list = data.get('items', [])
                        self.logger.info(f'Получено {len(stores_list)} магазинов')
                        return stores_list
                    else:
                        text = await response.text()
                        self.logger.error(f'Ошибка при получении списка магазинов: {response.status} - {text}')
                        raise Exception(f'Не удалось получить список магазинов: {response.status}')
        except Exception as e:
            self.logger.error(f'Исключение при получении списка магазинов: {e}')
            raise

    def get_store_id_by_address(self, address, stores_list):
        """
        Ищет storeId по адресу в списке магазинов.
        """
        self.logger.debug(f'Ищем storeId для адреса: {address}')
        self.logger.debug(f'Тип stores_list: {type(stores_list)}')
        if not isinstance(stores_list, list):
            self.logger.error(f'stores_list не является списком: {type(stores_list)}')
            return None
        
        for store in stores_list:
            self.logger.debug(f'Тип элемента: {type(store)}, значение: {store}')
            if isinstance(store, dict):
                if store.get('addressFull') == address:
                    return store.get('id')
            else:
                self.logger.warning(f'Элемент не является словарем: {type(store)}')
        
        self.logger.warning(f'Магазин с адресом "{address}" не найден в списке из {len(stores_list)} элементов')
        return None

    async def set_delivery_mode(self):
        """
        Выполняет POST запрос для установки режима доставки.
        Этот метод должен быть вызван один раз в начале работы.
        """
        if self.delivery_mode_set:
            self.logger.info('Режим доставки уже установлен, пропускаем')
            return
        
        # Получаем storeId для запроса на /delivery/mode/set
        delivery_store_id = self.store_id  # По умолчанию используем store_id паука
        
        if self.address:
            # Получаем список магазинов через API
            stores_list = await self.get_stores_list()
            
            # Ищем storeId по адресу
            found_store_id = self.get_store_id_by_address(self.address, stores_list)
            
            if found_store_id:
                delivery_store_id = found_store_id
                self.logger.info(f'Найден storeId {delivery_store_id} для адреса: {self.address}')
            else:
                self.logger.warning(f'Магазин с адресом "{self.address}" не найден, используется store_id по умолчанию: {delivery_store_id}')
        else:
            self.logger.warning(f'Адрес не указан, используется store_id по умолчанию: {delivery_store_id}')
        
        url = 'https://lenta.com/api-gateway/v1/delivery/mode/set'
        json_data = {
            'type': 'pickup',
            'storeId': delivery_store_id,
        }
        
        # Получаем заголовки с текущим sessiontoken
        headers = product_headers(self, self.sessiontoken)
        
        self.logger.info(f'Отправляем запрос на установку режима доставки для delivery_store_id: {delivery_store_id}')
        self.logger.info(f'URL: {url}')
        self.logger.info(f'Data: {json_data}')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=json_data,
                    headers=headers
                ) as response:
                    self.logger.info(f'Статус ответа: {response.status}')
                    if response.status == 200:
                        self.logger.info('Режим доставки успешно установлен')
                        self.delivery_mode_set = True
                    else:
                        text = await response.text()
                        self.logger.error(f'Ошибка при установке режима доставки: {response.status} - {text}')
        except Exception as e:
            self.logger.error(f'Исключение при установке режима доставки: {e}')
            raise

    async def start(self):
        # Устанавливаем режим доставки
        await self.set_delivery_mode()
        
        # Затем продолжаем обычный парсинг
        dict_url = self.get_redis_data(name_spider)

        # временное указание категорий, для тестовой выгрузки
        for category_id in [2, 754]:
            page_number = dict_url['page_number']

            json_data = {
                'categoryId': category_id,
                'filters': {
                    'checkbox': [],
                    'multicheckbox': [],
                    'range': [],
                },
                'sort': {
                    'type': 'popular',
                    'order': 'desc',
                },
                'limit': 40,
                'offset': 0,
            }

            yield Request(
                    url='https://lenta.com/api-gateway/v1/catalog/items',
                    headers=product_headers(self, self.sessiontoken),
                    callback=self.parse,
                    method='POST',
                    body=json.dumps(json_data),
                    dont_filter=True,
                    meta=self.attr_meta(
                        impersonate='firefox',
                        page_number=page_number,
                        category_id=category_id
                    ),
                )


    async def parse(self, response):
        page_number = response.meta['page_number']
        category_id = response.meta['category_id']

        data = json.loads(response.text)
        products = data['items']
        products_data = []

        for product in products:
            price = get_value(product, ['prices', 'costRegular'])
            price_card = get_value(product, ['prices', 'cost'])
            if price is not None:
                price = float(price) / 100
            if price_card is not None:
                price_card = float(price_card) / 100

            image = get_value(product, ['images', 0, 'large'])
            sku = get_value(product, ['id'])
            slug = get_value(product, ['slug'])
            url = f'https://lenta.com/product/{slug}-{sku}/'

            product_data = {
                'sku': get_value(product, ['id']),
                'title': get_value(product, ['name']),
                'price': price,
                'price_card': price_card,
                'url': url,
                'img_url': image,
                'created_at': datetime.now(),
            }
            products_data.append(product_data)

        item = CatalogItem()
        item['products_data'] = products_data
        yield item

        if len(products_data) == 0:
            return

        new_page_number = page_number + 1

        json_data = {
            'categoryId': category_id,
            'filters': {
                'checkbox': [],
                'multicheckbox': [],
                'range': [],
            },
            'sort': {
                'type': 'popular',
                'order': 'desc',
            },
            'limit': 40,
            'offset': new_page_number*40,
        }
        yield Request(
                url='https://lenta.com/api-gateway/v1/catalog/items',
                headers=product_headers(self, self.sessiontoken),
                callback=self.parse,
                method='POST',
                body=json.dumps(json_data),
                dont_filter=True,
                meta=self.attr_meta(
                    impersonate='firefox',
                    page_number=new_page_number,
                    category_id=category_id
                ),
            )
