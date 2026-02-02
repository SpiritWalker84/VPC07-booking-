"""
Бэкенд мини-системы бронирования.
"""
from typing import Optional, List
from postgres_driver import PostgresSQLDriver
from models import User, RestaurantTable, Booking

DB_NAME = "booking"


def _row_to_dict(cursor) -> List[dict]:
    """Преобразует результат курсора в список словарей."""
    columns = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _one_row_to_dict(cursor) -> Optional[dict]:
    """Преобразует одну строку результата в словарь или None."""
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [d[0] for d in cursor.description] if cursor.description else []
    return dict(zip(columns, row))


# --- create_tables ---


def create_tables() -> None:
    """Создаёт все таблицы по моделям (User, RestaurantTable, Booking)."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        db.create_table_from_model(User)
        db.create_table_from_model(RestaurantTable)
        db.create_table_from_model(Booking)


# --- Users CRUD ---


def create_user(email: str, first_name: str, last_name: str) -> Optional[int]:
    """Создаёт пользователя. Возвращает id или None."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, first_name, last_name) VALUES (%s, %s, %s) RETURNING id",
                    (email, first_name, last_name),
                )
                row = cur.fetchone()
                return row[0] if row else None


def get_user(user_id: int) -> Optional[dict]:
    """Возвращает пользователя по id или None."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, first_name, last_name FROM users WHERE id = %s", (user_id,))
                return _one_row_to_dict(cur)


def get_all_users() -> List[dict]:
    """Возвращает всех пользователей."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, first_name, last_name FROM users ORDER BY id")
                return _row_to_dict(cur)


def update_user(
    user_id: int,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> bool:
    """Обновляет пользователя. Возвращает True, если обновлена хотя бы одна строка."""
    updates = []
    args = []
    if email is not None:
        updates.append("email = %s")
        args.append(email)
    if first_name is not None:
        updates.append("first_name = %s")
        args.append(first_name)
    if last_name is not None:
        updates.append("last_name = %s")
        args.append(last_name)
    if not updates:
        return False
    args.append(user_id)
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = %s",
                    tuple(args),
                )
                return cur.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Удаляет пользователя. Возвращает True, если строка удалена."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                return cur.rowcount > 0


# --- Tables (restaurant_tables) CRUD ---


def create_table(table_number: int, capacity: int) -> Optional[int]:
    """Создаёт стол в ресторане. Возвращает id или None."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO restaurant_tables (table_number, capacity) VALUES (%s, %s) RETURNING id",
                    (table_number, capacity),
                )
                row = cur.fetchone()
                return row[0] if row else None


def get_table(table_id: int) -> Optional[dict]:
    """Возвращает стол по id или None."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, table_number, capacity FROM restaurant_tables WHERE id = %s",
                    (table_id,),
                )
                return _one_row_to_dict(cur)


def get_all_tables() -> List[dict]:
    """Возвращает все столы."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, table_number, capacity FROM restaurant_tables ORDER BY id")
                return _row_to_dict(cur)


def update_table(
    table_id: int,
    table_number: Optional[int] = None,
    capacity: Optional[int] = None,
) -> bool:
    """Обновляет стол. Возвращает True, если обновлена хотя бы одна строка."""
    updates = []
    args = []
    if table_number is not None:
        updates.append("table_number = %s")
        args.append(table_number)
    if capacity is not None:
        updates.append("capacity = %s")
        args.append(capacity)
    if not updates:
        return False
    args.append(table_id)
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE restaurant_tables SET {', '.join(updates)} WHERE id = %s",
                    tuple(args),
                )
                return cur.rowcount > 0


def delete_table(table_id: int) -> bool:
    """Удаляет стол. Возвращает True, если строка удалена."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM restaurant_tables WHERE id = %s", (table_id,))
                return cur.rowcount > 0


# --- Bookings CRUD ---


class BookingCapacityError(Exception):
    """Исключение: превышена вместимость стола на выбранные дату/время."""


def _check_table_capacity(cur, table_id: int, booking_date: str, booking_time: str, guests_count: int, exclude_booking_id: Optional[int] = None) -> None:
    """
    Проверяет, что добавление guests_count гостей на стол table_id в дату/время
    не превысит вместимость стола. Иначе выбрасывает BookingCapacityError.
    exclude_booking_id — при обновлении бронирования не учитывать это бронирование в сумме.
    """
    cur.execute(
        "SELECT capacity FROM restaurant_tables WHERE id = %s",
        (table_id,),
    )
    row = cur.fetchone()
    if not row:
        raise BookingCapacityError("Стол с таким ID не найден.")
    capacity = row[0]

    if exclude_booking_id is not None:
        cur.execute(
            """SELECT COALESCE(SUM(guests_count), 0) FROM bookings
               WHERE table_id = %s AND booking_date = %s AND booking_time = %s AND id != %s""",
            (table_id, booking_date, booking_time, exclude_booking_id),
        )
    else:
        cur.execute(
            """SELECT COALESCE(SUM(guests_count), 0) FROM bookings
               WHERE table_id = %s AND booking_date = %s AND booking_time = %s""",
            (table_id, booking_date, booking_time),
        )
    total = cur.fetchone()[0]
    if total + guests_count > capacity:
        raise BookingCapacityError(
            f"На это время стол уже забронирован: занято мест {total} из {capacity}. "
            f"Нельзя добавить ещё {guests_count} гостей."
        )


def create_booking(
    user_id: int,
    table_id: int,
    booking_date: str,
    booking_time: str,
    guests_count: int,
) -> Optional[int]:
    """Создаёт бронирование. Возвращает id или None. При превышении вместимости стола — BookingCapacityError."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                _check_table_capacity(cur, table_id, booking_date, booking_time, guests_count)
                cur.execute(
                    """INSERT INTO bookings (user_id, table_id, booking_date, booking_time, guests_count)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (user_id, table_id, booking_date, booking_time, guests_count),
                )
                row = cur.fetchone()
                return row[0] if row else None


def get_booking(booking_id: int) -> Optional[dict]:
    """Возвращает бронирование по id или None."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, user_id, table_id, booking_date, booking_time, guests_count, created_at
                       FROM bookings WHERE id = %s""",
                    (booking_id,),
                )
                return _one_row_to_dict(cur)


def get_all_bookings() -> List[dict]:
    """Возвращает все бронирования."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, user_id, table_id, booking_date, booking_time, guests_count, created_at
                       FROM bookings ORDER BY id"""
                )
                return _row_to_dict(cur)


def update_booking(
    booking_id: int,
    user_id: Optional[int] = None,
    table_id: Optional[int] = None,
    booking_date: Optional[str] = None,
    booking_time: Optional[str] = None,
    guests_count: Optional[int] = None,
) -> bool:
    """Обновляет бронирование. Возвращает True, если обновлена хотя бы одна строка. При превышении вместимости — BookingCapacityError."""
    updates = []
    args = []
    if user_id is not None:
        updates.append("user_id = %s")
        args.append(user_id)
    if table_id is not None:
        updates.append("table_id = %s")
        args.append(table_id)
    if booking_date is not None:
        updates.append("booking_date = %s")
        args.append(booking_date)
    if booking_time is not None:
        updates.append("booking_time = %s")
        args.append(booking_time)
    if guests_count is not None:
        updates.append("guests_count = %s")
        args.append(guests_count)
    if not updates:
        return False
    args.append(booking_id)
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_id, booking_date, booking_time, guests_count FROM bookings WHERE id = %s",
                    (booking_id,),
                )
                row = cur.fetchone()
                if not row:
                    return False
                eff_table = table_id if table_id is not None else row[0]
                eff_date = booking_date if booking_date is not None else str(row[1])
                eff_time = booking_time if booking_time is not None else str(row[2])
                eff_guests = guests_count if guests_count is not None else row[3]
                _check_table_capacity(cur, eff_table, eff_date, eff_time, eff_guests, exclude_booking_id=booking_id)
                cur.execute(
                    f"UPDATE bookings SET {', '.join(updates)} WHERE id = %s",
                    tuple(args),
                )
                return cur.rowcount > 0


def delete_booking(booking_id: int) -> bool:
    """Удаляет бронирование. Возвращает True, если строка удалена."""
    with PostgresSQLDriver(db_name=DB_NAME) as db:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
                return cur.rowcount > 0


if __name__ == "__main__":
    create_tables()
