import json
import logging
from datetime import datetime
from typing import Tuple

from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class CookieService:
    """Сервис для управления cookies"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
    
    def get_cookies(self, store_id: int) -> Tuple[str, str]:
        """Получение cookies и прокси для указанного магазина"""
        try:
            query = """SELECT cookies, proxy FROM cookies 
                      WHERE store_id = %s AND status = 'active' 
                      ORDER BY RANDOM() LIMIT 1"""
            
            result = self.db.execute_query(query, (store_id,))
            
            if not result:
                raise ValueError(f"Нет доступных cookies для store_id {store_id}")
            
            cookies, proxy = result[0]
            logger.debug(f"Получены cookies для store_id {store_id}")
            
            return cookies, proxy
            
        except Exception as e:
            logger.error(f"Ошибка при получении cookies для store_id {store_id}: {e}")
            raise
    
    def delete_cookie(self, store_id: int, proxy: str) -> bool:
        """Удаление cookies для указанного магазина и прокси"""
        try:
            query = """DELETE FROM cookies 
                      WHERE store_id = %s AND proxy = %s"""
            
            affected_rows = self.db.execute_update(query, (store_id, proxy))
            
            if affected_rows > 0:
                logger.info(f"Удалены cookies для store_id {store_id} и прокси {proxy}")
                return True
            else:
                logger.warning(f"Cookies для store_id {store_id} и прокси {proxy} не найдены")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при удалении cookies для store_id {store_id}: {e}")
            return False
    
    def clear_old_cookies(self, store_id: int) -> bool:
        """Очистка старых cookies для указанного магазина"""
        try:
            query = """DELETE FROM cookies WHERE store_id = %s"""
            
            affected_rows = self.db.execute_update(query, (store_id,))
            
            logger.info(f"Удалено {affected_rows} старых cookies для store_id {store_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых cookies для store_id {store_id}: {e}")
            return False
    
    def add_cookies(self, store_id: int, cookies: str, proxy: str, status: str = 'active') -> bool:
        """Добавление новых cookies"""
        try:
            query = """INSERT INTO cookies (store_id, cookies, proxy, status, date_added) 
                      VALUES (%s, %s, %s, %s, %s)
                      ON CONFLICT (proxy, store_id) 
                      DO UPDATE SET 
                          cookies = EXCLUDED.cookies,
                          status = EXCLUDED.status,
                          date_added = EXCLUDED.date_added"""
            
            params = (store_id, cookies, proxy, status, datetime.now())
            affected_rows = self.db.execute_update(query, params)
            
            logger.info(f"Добавлены/обновлены cookies для store_id {store_id} и прокси {proxy}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении cookies для store_id {store_id}: {e}")
            return False
    
    def update_cookie_status(self, store_id: int, proxy: str, status: str) -> bool:
        """Обновление статуса cookies"""
        try:
            query = """UPDATE cookies 
                      SET status = %s, last_used = CURRENT_TIMESTAMP 
                      WHERE store_id = %s AND proxy = %s"""
            
            affected_rows = self.db.execute_update(query, (status, store_id, proxy))
            
            if affected_rows > 0:
                logger.info(f"Обновлен статус cookies для store_id {store_id} и прокси {proxy} на {status}")
                return True
            else:
                logger.warning(f"Cookies для store_id {store_id} и прокси {proxy} не найдены")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса cookies для store_id {store_id}: {e}")
            return False
    
    def get_active_cookies_count(self, store_id: int) -> int:
        """Получение количества активных cookies для указанного магазина"""
        try:
            query = """SELECT COUNT(*) FROM cookies 
                      WHERE store_id = %s AND status = 'active'"""
            
            result = self.db.execute_query(query, (store_id,))
            count = result[0][0] if result else 0
            
            logger.debug(f"Количество активных cookies для store_id {store_id}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Ошибка при получении количества cookies для store_id {store_id}: {e}")
            return 0
    
    def validate_cookies(self, cookies: str) -> bool:
        """Валидация cookies"""
        try:
            if not cookies:
                return False
            
            # Проверяем, что cookies можно распарсить как JSON
            if isinstance(cookies, str):
                json.loads(cookies)
            
            return True
            
        except (json.JSONDecodeError, TypeError):
            logger.warning("Некорректный формат cookies")
            return False
