"""
Драйвер для работы с PostgreSQL базой данных.
"""
import os
import sys
from typing import Optional, List, Tuple, Type
from contextlib import contextmanager
from dotenv import load_dotenv

if sys.platform == "win32":
    postgres_paths = [
        r"C:\Program Files\PostgreSQL\17\bin",
        r"C:\Program Files\PostgreSQL\16\bin",
        r"C:\Program Files\PostgreSQL\15\bin",
        r"C:\Program Files\PostgreSQL\14\bin",
        r"C:\Program Files\PostgreSQL\13\bin",
    ]
    
    for postgres_bin in postgres_paths:
        if os.path.exists(postgres_bin):
            os.environ["PATH"] = postgres_bin + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(postgres_bin)
            except (AttributeError, OSError):
                pass
            break

import psycopg
from psycopg import errors


class PostgresDriver:
    """Драйвер для работы с PostgreSQL базой данных."""
    
    def __init__(self, 
                 db_host: Optional[str] = None,
                 db_port: Optional[str] = None,
                 db_name: Optional[str] = None,
                 db_user: Optional[str] = None,
                 db_password: Optional[str] = None):
        load_dotenv()
        
        self.db_host = db_host or os.getenv('DB_HOST', 'localhost')
        self.db_port = db_port or os.getenv('DB_PORT', '5432')
        self.db_name = db_name or os.getenv('DB_NAME', 'test')
        self.db_user = db_user or os.getenv('DB_USER', 'postgres')
        self.db_password = db_password or os.getenv('DB_PASSWORD', '')
        
        self.connection_string = (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password}"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения подключения к базе данных."""
        connection = None
        try:
            connection = psycopg.connect(self.connection_string)
            with connection.cursor() as cur:
                cur.execute("SET client_encoding TO 'UTF8'")
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()

    def create_table_if_not_exists(self, model: Type) -> None:
        """Создаёт таблицу по модели, если она не существует.
        model — класс модели с методом create_table_sql(), возвращающим SQL-строку (например, User).
        """
        sql: str = model.create_table_sql()
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)

    def create_table_from_model(self, model: Type) -> None:
        """Создаёт таблицу по модели, если она не существует.
        model — класс модели с методом create_table_sql(), возвращающим SQL-строку (например, User).
        """
        self.create_table_if_not_exists(model)
    
    def create_tables(self) -> None:
        """Создает таблицы users и orders в базе данных."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS orders CASCADE")
                cursor.execute("DROP TABLE IF EXISTS users CASCADE")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id   SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        age  INT  CHECK (age >= 0)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id         SERIAL PRIMARY KEY,
                        user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        amount     NUMERIC(10,2) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
    
    def add_user(self, name: str, age: int) -> int:
        """Добавляет пользователя в таблицу users."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id",
                    (name, age)
                )
                result = cursor.fetchone()
                return result[0] if result else None
    
    def add_order(self, user_id: int, amount: float) -> int:
        """Добавляет заказ в таблицу orders."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO orders (user_id, amount) VALUES (%s, %s) RETURNING id",
                    (user_id, amount)
                )
                result = cursor.fetchone()
                return result[0] if result else None
    
    def get_user_totals(self) -> List[Tuple[str, Optional[float]]]:
        """Получает сумму заказов по каждому пользователю (LEFT JOIN, сортировка по убыванию)."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        u.name,
                        COALESCE(SUM(o.amount), 0) as total_amount
                    FROM users u
                    LEFT JOIN orders o ON u.id = o.user_id
                    GROUP BY u.id, u.name
                    ORDER BY total_amount DESC
                """)
                return cursor.fetchall()


PostgresSQLDriver = PostgresDriver
