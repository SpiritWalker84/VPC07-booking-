"""
Модель объекта бронирования.
Связывает пользователя и стол с датой/временем бронирования.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Booking:
    """Бронирование стола в ресторане."""

    id: Optional[int]
    user_id: int          # внешняя связь с таблицей пользователей
    table_id: int         # внешняя связь с таблицей столов
    booking_date: str     # дата бронирования (DATE или ISO строка)
    booking_time: str     # время (TIME или строка)
    guests_count: int     # количество гостей
    created_at: Optional[datetime] = None

    @staticmethod
    def create_table_sql() -> str:
        """SQL для создания таблицы бронирований."""
        return """
            CREATE TABLE IF NOT EXISTS bookings (
                id            SERIAL PRIMARY KEY,
                user_id       INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                table_id      INT NOT NULL REFERENCES restaurant_tables(id) ON DELETE CASCADE,
                booking_date  DATE NOT NULL,
                booking_time  TIME NOT NULL,
                guests_count  INT NOT NULL CHECK (guests_count > 0),
                created_at    TIMESTAMP DEFAULT NOW()
            )
        """
