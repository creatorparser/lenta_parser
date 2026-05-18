import logging
import time
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from camoufox import AsyncCamoufox

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("camoufox_service")

app = FastAPI(title="Camoufox Scrape Service")

class ScrapeRequest(BaseModel):
    url: str
    proxy: Optional[str] = None
    wait_for_xpath: Optional[str] = None
    wait_for_timeout: int = 10000
    block_images: bool = True
    get_cookies: bool = True
    get_headers: bool = False

def parse_proxy(proxy_str: str) -> Optional[Dict]:
    if not proxy_str:
        return None
    if "://" not in proxy_str:
        raise ValueError("Proxy must contain scheme (http://, https://, socks5://)")
    scheme, rest = proxy_str.split("://", 1)
    if "@" in rest:
        auth, host = rest.split("@", 1)
        if ":" in auth:
            username, password = auth.split(":", 1)
        else:
            username, password = auth, ""
    else:
        username, password = None, None
        host = rest
    server = f"{scheme}://{host}"
    proxy_config = {"server": server}
    if username:
        proxy_config["username"] = username
        proxy_config["password"] = password
    return proxy_config

class HeaderCollector:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.headers = {}

    async def on_response(self, response):
        if response.url == self.target_url:
            self.headers.update(dict(response.headers))

@app.post("/scrape")
async def scrape_endpoint(req: ScrapeRequest):
    proxy_cfg = parse_proxy(req.proxy) if req.proxy else None

    try:
        async with AsyncCamoufox(
            headless="virtual",
            proxy=proxy_cfg,
            block_images=req.block_images,
        ) as browser:
            page = await browser.new_page()
            # await page.route("**/*", lambda route: route.abort()
            # if route.request.resource_type == "image"
            # else route.continue_())

            collector = None
            if req.get_headers:
                collector = HeaderCollector(req.url)
                page.on("response", collector.on_response)

            logger.info(f"🌐 Переход: {req.url}")
            response = await page.goto(req.url, timeout=req.wait_for_timeout)

            if req.wait_for_xpath:
                try:
                    await page.wait_for_selector(
                        f"xpath={req.wait_for_xpath}",
                        timeout=req.wait_for_timeout
                    )
                    logger.info(f"✅ XPath найден: {req.wait_for_xpath}")
                except Exception as e:
                    logger.warning(f"⚠️ XPath не дождались: {e}")
            time.sleep(7)
            html = await page.content()

            cookies = {}
            if req.get_cookies:
                try:
                    all_cookies = await page.context.cookies()
                    cookies = {c["name"]: c["value"] for c in all_cookies}
                except Exception as e:
                    logger.error(f"Ошибка получения кук: {e}")

            request_headers = dict(response.request.headers)   # <-- добавлено

            result = {
                "html": html,
                "cookies": cookies,
                "headers": request_headers,            # <-- добавлено
                "headers_response": collector.headers if collector else {},
                "status": "success"
            }
            logger.info(f"✅ Успешно для {req.url}")
            return result

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))