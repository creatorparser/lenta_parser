import json
import logging
import os
import re
from datetime import datetime

import requests
from lxml.html import HtmlElement
from scrapy import Selector
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)


def get_value(my_dict, keys: list):
    try:
        value = my_dict
        for key in keys:
            if key is None or value is None:
                return None
            if isinstance(key, int) and key + 1 > len(value):
                return None
            value = value[key]
        return value
    except KeyError or TypeError or IndexError:
        return None


def notifier_telegram(settings, message):
    token = settings['TOKEN']
    chat_id = settings['CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)


def get_all_str(file_path):
    """
    Читает строки из файла и возвращает их в виде списка.

    Args:
        file_path: Путь к файлу для чтения

    Returns:
        Список строк из файла. Если файл не существует, возвращает пустой список.
    """
    if not os.path.exists(file_path):
        logger.warning(f"Файл не найден: {file_path}. Возвращается пустой список.")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
            logger.info(f"Загружено {len(lines)} строк из файла {file_path}")
            return lines
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return []