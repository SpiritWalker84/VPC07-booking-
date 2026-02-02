"""
Модель стола для бронирования в ресторане.
Каждый экземпляр описывает один конкретный стол в ресторане.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RestaurantTable:
    """Стол в ресторане (один конкретный стол для бронирования)."""

    id: Optional[int]
    table_number: int   # номер стола
    capacity: int       # количество мест (гостей)

    @staticmethod
    def create_table_sql() -> str:
        """SQL для создания таблицы столов."""
        return """
            CREATE TABLE IF NOT EXISTS restaurant_tables (
                id           SERIAL PRIMARY KEY,
                table_number INT NOT NULL UNIQUE,
                capacity     INT NOT NULL CHECK (capacity > 0)
            )
        """
