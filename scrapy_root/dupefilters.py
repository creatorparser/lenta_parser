import hashlib

from scrapy.dupefilters import RFPDupeFilter
from scrapy.utils.python import to_bytes


class SimpleBodyDupeFilter(RFPDupeFilter):
    """Простейший фильтр дубликатов по телу запроса"""

    def request_fingerprint(self, request):
        # Всегда включаем метод в fingerprint
        if request.method == 'POST' and request.body:
            # Для POST с телом: метод + URL + тело
            fp_parts = [
                request.method.encode('utf-8'),
                to_bytes(request.url),
                request.body  # Просто добавляем тело как есть
            ]
            # Собираем все части и хешируем
            fp_string = b'|'.join(fp_parts)
            return hashlib.sha1(fp_string).digest()
        return None