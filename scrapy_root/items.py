from scrapy.item import Item, Field


class CatalogItem(Item):
    products_data = Field()


class CookiesHeadersItem(Item):
    start_time = Field()
    request_url = Field()
    spider = Field()
    store_id = Field()
    meta = Field()
    cookies = Field()
    headers = Field()
    proxy = Field()
    type_proxy = Field()
    provider_proxy = Field()
