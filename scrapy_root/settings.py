import os

from dotenv import load_dotenv

load_dotenv()

HOSTNAME_POSTGRESQL = os.environ.get('HOSTNAME_POSTGRESQL')
USERNAME_POSTGRESQL = os.environ.get('USERNAME_POSTGRESQL')
PASSWORD_POSTGRESQL = os.environ.get('PASSWORD_POSTGRESQL')
DATABASE_POSTGRESQL = os.environ.get('DATABASE_POSTGRESQL')
PORT_POSTGRESQL = os.environ.get('PORT_POSTGRESQL')
PORT_REDIS = os.environ.get('PORT_REDIS')

ITEM_PIPELINES = {
    'scrapy_root.pipelines.CatalogPipeline': 300,
}

LOG_ENABLED = True
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

ROBOTSTXT_OBEY = False
FEED_EXPORT_ENCODING = "utf-8"

SPIDER_MODULES = [
    'scrapy_root.spiders.lenta',
]

DOWNLOAD_HANDLERS = {
    "http": "scrapy_root.handlers.scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_root.handlers.scrapy_impersonate.ImpersonateDownloadHandler",
}

TWISTED_REACTOR =  "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_TIMEOUT = 60
RETRY_TIMES = 5
RETRY_ENABLED = True
RETRY_HTTP_CODES = [
    500, 502, 503, 504, 507, 510, 400, 404, 408, 429, 520, 521, 522, 523, 524, 525, 526
]

DOWNLOAD_DELAY = 5
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# --- ТАЙМЕР НА 4 ЧАСА ---
CLOSESPIDER_TIMEOUT = 18000

IMPERSONATE = 'chrome'

USER_AGENT = None
