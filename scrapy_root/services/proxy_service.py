import logging
import random
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ProxyService:
    """Сервис для управления прокси"""
    
    def __init__(self, proxy_file_path: Optional[str] = None):
        self.proxy_file_path = proxy_file_path or 'files/list_proxies.txt'
        self._proxies = []
        self._load_proxies()
    
    def _load_proxies(self):
        """Загрузка списка прокси из файла"""
        try:
            proxy_file = Path(self.proxy_file_path)
            if proxy_file.exists():
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    self._proxies = [line.strip() for line in f if line.strip()]
                logger.info(f"Загружено {len(self._proxies)} прокси из файла {self.proxy_file_path}")
            else:
                logger.warning(f"Файл с прокси не найден: {self.proxy_file_path}")
                self._proxies = []
        except Exception as e:
            logger.error(f"Ошибка при загрузке прокси: {e}")
            self._proxies = []
    
    def get_random_proxy(self) -> Optional[str]:
        """Получение случайного прокси"""
        if not self._proxies:
            logger.warning("Список прокси пуст")
            return None
        
        proxy = random.choice(self._proxies)
        logger.debug(f"Выбран прокси: {proxy}")
        return proxy
    
    def get_proxy_list(self) -> List[str]:
        """Получение списка всех прокси"""
        return self._proxies.copy()
    
    def add_proxy(self, proxy: str) -> bool:
        """Добавление нового прокси"""
        try:
            if proxy not in self._proxies:
                self._proxies.append(proxy)
                self._save_proxies()
                logger.info(f"Добавлен новый прокси: {proxy}")
                return True
            else:
                logger.debug(f"Прокси уже существует: {proxy}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении прокси {proxy}: {e}")
            return False
    
    def remove_proxy(self, proxy: str) -> bool:
        """Удаление прокси"""
        try:
            if proxy in self._proxies:
                self._proxies.remove(proxy)
                self._save_proxies()
                logger.info(f"Удален прокси: {proxy}")
                return True
            else:
                logger.debug(f"Прокси не найден: {proxy}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при удалении прокси {proxy}: {e}")
            return False
    
    def _save_proxies(self):
        """Сохранение списка прокси в файл"""
        try:
            proxy_file = Path(self.proxy_file_path)
            proxy_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(proxy_file, 'w', encoding='utf-8') as f:
                for proxy in self._proxies:
                    f.write(f"{proxy}\n")
            
            logger.debug(f"Список прокси сохранен в файл {self.proxy_file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении прокси: {e}")
    
    def reload_proxies(self):
        """Перезагрузка списка прокси из файла"""
        logger.info("Перезагрузка списка прокси")
        self._load_proxies()
    
    def get_proxy_count(self) -> int:
        """Получение количества доступных прокси"""
        return len(self._proxies)
    
    def is_proxy_available(self, proxy: str) -> bool:
        """Проверка доступности прокси"""
        return proxy in self._proxies
    
    def get_proxy_info(self, proxy: str) -> Optional[Dict[str, Any]]:
        """Получение информации о прокси"""
        if not self.is_proxy_available(proxy):
            return None
        
        try:
            # Парсинг прокси для получения информации
            if '@' in proxy:
                auth_part, ip_part = proxy.split('@')
                username, password = auth_part.split(':')
                ip, port = ip_part.split(':')
                
                return {
                    'username': username,
                    'password': password,
                    'ip': ip,
                    'port': port,
                    'full_proxy': proxy
                }
            else:
                ip, port = proxy.split(':')
                return {
                    'username': None,
                    'password': None,
                    'ip': ip,
                    'port': port,
                    'full_proxy': proxy
                }
        except Exception as e:
            logger.error(f"Ошибка при парсинге прокси {proxy}: {e}")
            return None
