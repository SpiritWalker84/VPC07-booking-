"""
Модель пользователя мини-системы бронирования.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Пользователь системы бронирования."""

    id: Optional[int]
    email: str
    first_name: str  # имя
    last_name: str   # фамилия

    @staticmethod
    def create_table_sql() -> str:
        """SQL для создания таблицы пользователей."""
        return """
            CREATE TABLE IF NOT EXISTS users (
                id         SERIAL PRIMARY KEY,
                email      VARCHAR(255) NOT NULL UNIQUE,
                first_name VARCHAR(100) NOT NULL,
                last_name  VARCHAR(100) NOT NULL
            )
        """
