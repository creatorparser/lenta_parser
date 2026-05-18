import logging
from contextlib import contextmanager
from typing import Optional, Any, List

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DatabaseService:
    """Сервис для управления соединениями с базой данных"""
    
    def __init__(self, hostname: str, username: str, password: str, 
                 database: str, port: str, min_conn: int = 1, max_conn: int = 20):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database = database
        self.port = port
        self.min_conn = min_conn
        self.max_conn = max_conn
        
        self._connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Инициализация пула соединений"""
        try:
            self._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=self.min_conn,
                maxconn=self.max_conn,
                user=self.username,
                password=self.password,
                host=self.hostname,
                database=self.database,
                port=self.port
            )
            logger.info("Пул соединений с базой данных успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации пула соединений: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения соединения"""
        connection = None
        try:
            connection = self._connection_pool.getconn()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Ошибка при работе с соединением: {e}")
            raise
        finally:
            if connection:
                self._connection_pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для получения курсора"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                yield cursor, connection
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Выполнение SELECT запроса"""
        with self.get_cursor() as (cursor, connection):
            try:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result
            except Exception as e:
                logger.error(f"Ошибка при выполнении запроса: {e}")
                connection.rollback()
                raise


    def execute_update(self, query: str, params: Optional[dict] = None) -> int:
        """Выполнение UPDATE/INSERT/DELETE запроса с использованием именованных параметров"""
        with self.get_cursor() as (cursor, connection):
            try:
                cursor.execute(query, params)
                connection.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Ошибка при выполнении обновления: {e}")
                connection.rollback()
                raise

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Выполнение множественных запросов"""
        with self.get_cursor() as (cursor, connection):
            try:
                cursor.executemany(query, params_list)
                connection.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Ошибка при выполнении множественных запросов: {e}")
                connection.rollback()
                raise

    def upsert_record(self, table: str, data: dict, conflict_column: str,
                      return_column: str, update_columns: Optional[str] = None) -> Any:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        # Добавляем обработку конфликта
        if update_columns:
            query += f" ON CONFLICT ({conflict_column}) DO UPDATE SET {update_columns} RETURNING {return_column}"
        else:
            query += f" ON CONFLICT ({conflict_column}) DO NOTHING RETURNING {return_column}"

        # Запрос для получения существующей записи при DO NOTHING
        select_query = f"SELECT {return_column} FROM {table} WHERE {conflict_column} = %s"

        with self.get_cursor() as (cursor, connection):
            try:
                # Выполняем UPSERT операцию
                cursor.execute(query, list(data.values()))
                result = cursor.fetchone()

                # Если запись не была вставлена/обновлена (DO NOTHING)
                if result is None:
                    cursor.execute(select_query, (data[conflict_column],))
                    result = cursor.fetchone()
                    if result is None:
                        raise ValueError(
                            f"Запись с {conflict_column}={data[conflict_column]} "
                            "не найдена после операции UPSERT"
                        )

                # Фиксируем изменения
                connection.commit()
                return result[0]

            except Exception as e:
                connection.rollback()
                logger.error(f"Ошибка при выполнении UPSERT операции: {e}")
                raise


    def close(self):
        """Закрытие пула соединений"""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("Пул соединений с базой данных закрыт")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
