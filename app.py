"""
Графический интерфейс системы бронирования (tkinter).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import backend


def _safe_int(value: str, default=None):
    try:
        return int(value.strip()) if value.strip() else default
    except ValueError:
        return None


def _show_result(msg: str, is_error: bool = False):
    if is_error:
        messagebox.showerror("Ошибка", msg)
    else:
        messagebox.showinfo("Результат", msg)


def _date_ru_to_db(s: str):
    """ДД-ММ-ГГГГ -> YYYY-MM-DD для PostgreSQL. Возвращает None при ошибке."""
    s = s.strip()
    if not s:
        return None
    parts = s.split("-")
    if len(parts) != 3:
        return None
    try:
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        if 1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2100:
            return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        pass
    return None


def _date_db_to_ru(val):
    """Дата из БД (str YYYY-MM-DD или date) -> ДД-ММ-ГГГГ для отображения."""
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    parts = s.split("-")
    if len(parts) == 3 and len(parts[0]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return s


# --- Вкладка «Пользователи» ---


def build_users_tab(parent):
    frame = ttk.Frame(parent, padding=10)

    # Инициализация БД
    grp_init = ttk.Frame(frame)
    grp_init.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    def do_create_tables():
        try:
            backend.create_tables()
            _show_result("Таблицы созданы или уже существуют.")
        except Exception as ex:
            _show_result(str(ex), is_error=True)
    ttk.Button(grp_init, text="Создать таблицы в БД", command=do_create_tables).pack(side=tk.LEFT, padx=(0, 10))

    # Создать
    grp_create = ttk.LabelFrame(frame, text="Создать пользователя", padding=5)
    grp_create.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ttk.Label(grp_create, text="Email:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_email = ttk.Entry(grp_create, width=30)
    ent_email.grid(row=0, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="Имя:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    ent_first = ttk.Entry(grp_create, width=30)
    ent_first.grid(row=1, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="Фамилия:").grid(row=2, column=0, sticky="w", padx=(0, 5))
    ent_last = ttk.Entry(grp_create, width=30)
    ent_last.grid(row=2, column=1, padx=(0, 15))

    def do_create_user():
        e, f, l = ent_email.get().strip(), ent_first.get().strip(), ent_last.get().strip()
        if not e or not f or not l:
            _show_result("Заполните email, имя и фамилию.", is_error=True)
            return
        try:
            uid = backend.create_user(e, f, l)
            if uid is not None:
                _show_result(f"Пользователь создан, id = {uid}")
                ent_email.delete(0, tk.END)
                ent_first.delete(0, tk.END)
                ent_last.delete(0, tk.END)
            else:
                _show_result("Не удалось создать пользователя.", is_error=True)
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_create, text="Создать", command=do_create_user).grid(row=3, column=1, pady=(5, 0))

    # Найти по ID
    grp_get = ttk.LabelFrame(frame, text="Найти по ID", padding=5)
    grp_get.grid(row=2, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_get, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_user_id = ttk.Entry(grp_get, width=10)
    ent_user_id.grid(row=0, column=1, padx=(0, 10))
    txt_user = ScrolledText(grp_get, height=4, width=40, state="disabled")
    txt_user.grid(row=1, column=0, columnspan=2, pady=(5, 0))

    def do_get_user():
        uid = _safe_int(ent_user_id.get())
        if uid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        try:
            u = backend.get_user(uid)
            txt_user.config(state="normal")
            txt_user.delete(1.0, tk.END)
            if u:
                txt_user.insert(tk.END, "\n".join(f"{k}: {v}" for k, v in u.items()))
            else:
                txt_user.insert(tk.END, "Не найдено.")
            txt_user.config(state="disabled")
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_get, text="Найти", command=do_get_user).grid(row=0, column=2, padx=(5, 0))

    # Список всех
    grp_list_u = ttk.LabelFrame(frame, text="Все пользователи", padding=5)
    grp_list_u.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
    columns_u = ("id", "email", "first_name", "last_name")
    tree_u = ttk.Treeview(grp_list_u, columns=columns_u, show="headings", height=6)
    for c in columns_u:
        tree_u.heading(c, text={"id": "ID", "email": "Email", "first_name": "Имя", "last_name": "Фамилия"}[c])
        tree_u.column(c, width=80)
    tree_u.column("email", width=180)
    tree_u.grid(row=0, column=0, sticky="nsew")
    sb_u = ttk.Scrollbar(grp_list_u, orient=tk.VERTICAL, command=tree_u.yview)
    sb_u.grid(row=0, column=1, sticky="ns")
    tree_u.configure(yscrollcommand=sb_u.set)

    def do_list_users():
        for i in tree_u.get_children():
            tree_u.delete(i)
        try:
            for row in backend.get_all_users():
                tree_u.insert("", tk.END, values=(row["id"], row["email"], row["first_name"], row["last_name"]))
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_list_u, text="Обновить список", command=do_list_users).grid(row=1, column=0, pady=(5, 0))

    # Обновить
    grp_upd_u = ttk.LabelFrame(frame, text="Обновить пользователя", padding=5)
    grp_upd_u.grid(row=4, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_upd_u, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_upd_uid = ttk.Entry(grp_upd_u, width=10)
    ent_upd_uid.grid(row=0, column=1, padx=(0, 10))
    ttk.Label(grp_upd_u, text="Email:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    ent_upd_email = ttk.Entry(grp_upd_u, width=25)
    ent_upd_email.grid(row=1, column=1, padx=(0, 10))
    ttk.Label(grp_upd_u, text="Имя:").grid(row=2, column=0, sticky="w", padx=(0, 5))
    ent_upd_first = ttk.Entry(grp_upd_u, width=25)
    ent_upd_first.grid(row=2, column=1, padx=(0, 10))
    ttk.Label(grp_upd_u, text="Фамилия:").grid(row=3, column=0, sticky="w", padx=(0, 5))
    ent_upd_last = ttk.Entry(grp_upd_u, width=25)
    ent_upd_last.grid(row=3, column=1, padx=(0, 10))

    def do_update_user():
        uid = _safe_int(ent_upd_uid.get())
        if uid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        email = ent_upd_email.get().strip() or None
        first = ent_upd_first.get().strip() or None
        last = ent_upd_last.get().strip() or None
        if not any([email, first, last]):
            _show_result("Укажите хотя бы одно поле для обновления.", is_error=True)
            return
        try:
            ok = backend.update_user(uid, email=email, first_name=first, last_name=last)
            _show_result("Обновлено." if ok else "Запись не найдена или не изменена.")
            if ok:
                do_list_users()
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_upd_u, text="Обновить", command=do_update_user).grid(row=4, column=1, pady=(5, 0))

    # Удалить
    grp_del_u = ttk.LabelFrame(frame, text="Удалить пользователя", padding=5)
    grp_del_u.grid(row=5, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_del_u, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_del_uid = ttk.Entry(grp_del_u, width=10)
    ent_del_uid.grid(row=0, column=1, padx=(0, 10))

    def do_delete_user():
        uid = _safe_int(ent_del_uid.get())
        if uid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        if not messagebox.askyesno("Подтверждение", "Удалить пользователя?"):
            return
        try:
            ok = backend.delete_user(uid)
            _show_result("Удалено." if ok else "Запись не найдена.")
            if ok:
                do_list_users()
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_del_u, text="Удалить", command=do_delete_user).grid(row=0, column=2, padx=(5, 0))

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(3, weight=1)
    return frame


# --- Вкладка «Столы» ---


def build_tables_tab(parent):
    frame = ttk.Frame(parent, padding=10)

    grp_create = ttk.LabelFrame(frame, text="Создать стол", padding=5)
    grp_create.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ttk.Label(grp_create, text="Номер стола:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_num = ttk.Entry(grp_create, width=10)
    ent_num.grid(row=0, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="Вместимость:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    ent_cap = ttk.Entry(grp_create, width=10)
    ent_cap.grid(row=1, column=1, padx=(0, 15))

    def do_create_table():
        num, cap = _safe_int(ent_num.get()), _safe_int(ent_cap.get())
        if num is None or cap is None:
            _show_result("Введите число для номера и вместимости.", is_error=True)
            return
        if cap < 1:
            _show_result("Вместимость должна быть > 0.", is_error=True)
            return
        try:
            tid = backend.create_table(num, cap)
            if tid is not None:
                _show_result(f"Стол создан, id = {tid}")
                ent_num.delete(0, tk.END)
                ent_cap.delete(0, tk.END)
            else:
                _show_result("Не удалось создать стол (возможно, такой номер уже есть).", is_error=True)
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_create, text="Создать", command=do_create_table).grid(row=2, column=1, pady=(5, 0))

    grp_get = ttk.LabelFrame(frame, text="Найти по ID", padding=5)
    grp_get.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_get, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_tid = ttk.Entry(grp_get, width=10)
    ent_tid.grid(row=0, column=1, padx=(0, 10))
    txt_t = ScrolledText(grp_get, height=3, width=35, state="disabled")
    txt_t.grid(row=1, column=0, columnspan=2, pady=(5, 0))

    def do_get_table():
        tid = _safe_int(ent_tid.get())
        if tid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        try:
            t = backend.get_table(tid)
            txt_t.config(state="normal")
            txt_t.delete(1.0, tk.END)
            if t:
                txt_t.insert(tk.END, "\n".join(f"{k}: {v}" for k, v in t.items()))
            else:
                txt_t.insert(tk.END, "Не найдено.")
            txt_t.config(state="disabled")
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_get, text="Найти", command=do_get_table).grid(row=0, column=2, padx=(5, 0))

    grp_list_t = ttk.LabelFrame(frame, text="Все столы", padding=5)
    grp_list_t.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
    columns_t = ("id", "table_number", "capacity")
    tree_t = ttk.Treeview(grp_list_t, columns=columns_t, show="headings", height=6)
    for c in columns_t:
        tree_t.heading(c, text={"id": "ID", "table_number": "Номер", "capacity": "Вместимость"}[c])
        tree_t.column(c, width=100)
    tree_t.grid(row=0, column=0, sticky="nsew")
    sb_t = ttk.Scrollbar(grp_list_t, orient=tk.VERTICAL, command=tree_t.yview)
    sb_t.grid(row=0, column=1, sticky="ns")
    tree_t.configure(yscrollcommand=sb_t.set)

    def do_list_tables():
        for i in tree_t.get_children():
            tree_t.delete(i)
        try:
            for row in backend.get_all_tables():
                tree_t.insert("", tk.END, values=(row["id"], row["table_number"], row["capacity"]))
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_list_t, text="Обновить список", command=do_list_tables).grid(row=1, column=0, pady=(5, 0))

    grp_upd_t = ttk.LabelFrame(frame, text="Обновить стол", padding=5)
    grp_upd_t.grid(row=3, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_upd_t, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_upd_tid = ttk.Entry(grp_upd_t, width=10)
    ent_upd_tid.grid(row=0, column=1, padx=(0, 10))
    ttk.Label(grp_upd_t, text="Номер:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    ent_upd_num = ttk.Entry(grp_upd_t, width=10)
    ent_upd_num.grid(row=1, column=1, padx=(0, 10))
    ttk.Label(grp_upd_t, text="Вместимость:").grid(row=2, column=0, sticky="w", padx=(0, 5))
    ent_upd_cap = ttk.Entry(grp_upd_t, width=10)
    ent_upd_cap.grid(row=2, column=1, padx=(0, 10))

    def do_update_table():
        tid = _safe_int(ent_upd_tid.get())
        if tid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        num, cap = _safe_int(ent_upd_num.get()), _safe_int(ent_upd_cap.get())
        if num is None and cap is None:
            _show_result("Укажите номер и/или вместимость.", is_error=True)
            return
        try:
            ok = backend.update_table(tid, table_number=num, capacity=cap)
            _show_result("Обновлено." if ok else "Запись не найдена или не изменена.")
            if ok:
                do_list_tables()
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_upd_t, text="Обновить", command=do_update_table).grid(row=3, column=1, pady=(5, 0))

    grp_del_t = ttk.LabelFrame(frame, text="Удалить стол", padding=5)
    grp_del_t.grid(row=4, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_del_t, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_del_tid = ttk.Entry(grp_del_t, width=10)
    ent_del_tid.grid(row=0, column=1, padx=(0, 10))

    def do_delete_table():
        tid = _safe_int(ent_del_tid.get())
        if tid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        if not messagebox.askyesno("Подтверждение", "Удалить стол?"):
            return
        try:
            ok = backend.delete_table(tid)
            _show_result("Удалено." if ok else "Запись не найдена.")
            if ok:
                do_list_tables()
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_del_t, text="Удалить", command=do_delete_table).grid(row=0, column=2, padx=(5, 0))

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)
    return frame


# --- Вкладка «Бронирования» ---


def build_bookings_tab(parent):
    frame = ttk.Frame(parent, padding=10)

    grp_create = ttk.LabelFrame(frame, text="Создать бронирование", padding=5)
    grp_create.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ttk.Label(grp_create, text="ID пользователя:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_b_user = ttk.Entry(grp_create, width=10)
    ent_b_user.grid(row=0, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="ID стола:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    ent_b_table = ttk.Entry(grp_create, width=10)
    ent_b_table.grid(row=1, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="Дата (ДД-ММ-ГГГГ):").grid(row=2, column=0, sticky="w", padx=(0, 5))
    ent_b_date = ttk.Entry(grp_create, width=15)
    ent_b_date.grid(row=2, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="Время (HH:MM или HH:MM:SS):").grid(row=3, column=0, sticky="w", padx=(0, 5))
    ent_b_time = ttk.Entry(grp_create, width=15)
    ent_b_time.grid(row=3, column=1, padx=(0, 15))
    ttk.Label(grp_create, text="Кол-во гостей:").grid(row=4, column=0, sticky="w", padx=(0, 5))
    ent_b_guests = ttk.Entry(grp_create, width=10)
    ent_b_guests.grid(row=4, column=1, padx=(0, 15))

    def do_create_booking():
        uid = _safe_int(ent_b_user.get())
        tid = _safe_int(ent_b_table.get())
        date_ru = ent_b_date.get().strip()
        time = ent_b_time.get().strip()
        guests = _safe_int(ent_b_guests.get())
        if uid is None or tid is None:
            _show_result("Введите ID пользователя и ID стола.", is_error=True)
            return
        if not date_ru or not time:
            _show_result("Введите дату и время.", is_error=True)
            return
        date = _date_ru_to_db(date_ru)
        if date is None:
            _show_result("Дата в формате ДД-ММ-ГГГГ (например 25-12-2025).", is_error=True)
            return
        if guests is None or guests < 1:
            _show_result("Количество гостей должно быть > 0.", is_error=True)
            return
        try:
            bid = backend.create_booking(uid, tid, date, time, guests)
            if bid is not None:
                _show_result(f"Бронирование создано, id = {bid}")
                ent_b_user.delete(0, tk.END)
                ent_b_table.delete(0, tk.END)
                ent_b_date.delete(0, tk.END)
                ent_b_time.delete(0, tk.END)
                ent_b_guests.delete(0, tk.END)
            else:
                _show_result("Не удалось создать бронирование.", is_error=True)
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_create, text="Создать", command=do_create_booking).grid(row=5, column=1, pady=(5, 0))

    grp_get = ttk.LabelFrame(frame, text="Найти по ID", padding=5)
    grp_get.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_get, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_bid = ttk.Entry(grp_get, width=10)
    ent_bid.grid(row=0, column=1, padx=(0, 10))
    txt_b = ScrolledText(grp_get, height=5, width=45, state="disabled")
    txt_b.grid(row=1, column=0, columnspan=2, pady=(5, 0))

    def do_get_booking():
        bid = _safe_int(ent_bid.get())
        if bid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        try:
            b = backend.get_booking(bid)
            txt_b.config(state="normal")
            txt_b.delete(1.0, tk.END)
            if b:
                for k, v in b.items():
                    if k == "booking_date":
                        v = _date_db_to_ru(v)
                    txt_b.insert(tk.END, f"{k}: {v}\n")
            else:
                txt_b.insert(tk.END, "Не найдено.")
            txt_b.config(state="disabled")
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_get, text="Найти", command=do_get_booking).grid(row=0, column=2, padx=(5, 0))

    grp_list_b = ttk.LabelFrame(frame, text="Все бронирования", padding=5)
    grp_list_b.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
    columns_b = ("id", "user_id", "table_id", "booking_date", "booking_time", "guests_count")
    tree_b = ttk.Treeview(grp_list_b, columns=columns_b, show="headings", height=6)
    heads_b = {"id": "ID", "user_id": "User ID", "table_id": "Table ID", "booking_date": "Дата", "booking_time": "Время", "guests_count": "Гостей"}
    for c in columns_b:
        tree_b.heading(c, text=heads_b[c])
        tree_b.column(c, width=70)
    tree_b.grid(row=0, column=0, sticky="nsew")
    sb_b = ttk.Scrollbar(grp_list_b, orient=tk.VERTICAL, command=tree_b.yview)
    sb_b.grid(row=0, column=1, sticky="ns")
    tree_b.configure(yscrollcommand=sb_b.set)

    def do_list_bookings():
        for i in tree_b.get_children():
            tree_b.delete(i)
        try:
            for row in backend.get_all_bookings():
                tree_b.insert("", tk.END, values=(
                    row["id"], row["user_id"], row["table_id"],
                    _date_db_to_ru(row.get("booking_date")),
                    str(row["booking_time"]) if row.get("booking_time") else "",
                    row["guests_count"],
                ))
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_list_b, text="Обновить список", command=do_list_bookings).grid(row=1, column=0, pady=(5, 0))

    grp_upd_b = ttk.LabelFrame(frame, text="Обновить бронирование", padding=5)
    grp_upd_b.grid(row=3, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_upd_b, text="ID бронирования:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_upd_bid = ttk.Entry(grp_upd_b, width=10)
    ent_upd_bid.grid(row=0, column=1, padx=(0, 10))
    ttk.Label(grp_upd_b, text="User ID:").grid(row=1, column=0, sticky="w", padx=(0, 5))
    ent_upd_uid_b = ttk.Entry(grp_upd_b, width=10)
    ent_upd_uid_b.grid(row=1, column=1, padx=(0, 10))
    ttk.Label(grp_upd_b, text="Table ID:").grid(row=2, column=0, sticky="w", padx=(0, 5))
    ent_upd_tid_b = ttk.Entry(grp_upd_b, width=10)
    ent_upd_tid_b.grid(row=2, column=1, padx=(0, 10))
    ttk.Label(grp_upd_b, text="Дата (ДД-ММ-ГГГГ):").grid(row=3, column=0, sticky="w", padx=(0, 5))
    ent_upd_date_b = ttk.Entry(grp_upd_b, width=15)
    ent_upd_date_b.grid(row=3, column=1, padx=(0, 10))
    ttk.Label(grp_upd_b, text="Время:").grid(row=4, column=0, sticky="w", padx=(0, 5))
    ent_upd_time_b = ttk.Entry(grp_upd_b, width=15)
    ent_upd_time_b.grid(row=4, column=1, padx=(0, 10))
    ttk.Label(grp_upd_b, text="Гостей:").grid(row=5, column=0, sticky="w", padx=(0, 5))
    ent_upd_guests_b = ttk.Entry(grp_upd_b, width=10)
    ent_upd_guests_b.grid(row=5, column=1, padx=(0, 10))

    def do_update_booking():
        bid = _safe_int(ent_upd_bid.get())
        if bid is None:
            _show_result("Введите ID бронирования.", is_error=True)
            return
        uid = _safe_int(ent_upd_uid_b.get())
        tid = _safe_int(ent_upd_tid_b.get())
        date_ru = ent_upd_date_b.get().strip() or None
        date = _date_ru_to_db(date_ru) if date_ru else None
        if date_ru and date is None:
            _show_result("Дата в формате ДД-ММ-ГГГГ.", is_error=True)
            return
        time = ent_upd_time_b.get().strip() or None
        guests = _safe_int(ent_upd_guests_b.get())
        if not any([uid is not None, tid is not None, date, time, guests is not None]):
            _show_result("Укажите хотя бы одно поле для обновления.", is_error=True)
            return
        try:
            ok = backend.update_booking(bid, user_id=uid, table_id=tid, booking_date=date, booking_time=time, guests_count=guests)
            _show_result("Обновлено." if ok else "Запись не найдена или не изменена.")
            if ok:
                do_list_bookings()
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_upd_b, text="Обновить", command=do_update_booking).grid(row=6, column=1, pady=(5, 0))

    grp_del_b = ttk.LabelFrame(frame, text="Удалить бронирование", padding=5)
    grp_del_b.grid(row=4, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(grp_del_b, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ent_del_bid = ttk.Entry(grp_del_b, width=10)
    ent_del_bid.grid(row=0, column=1, padx=(0, 10))

    def do_delete_booking():
        bid = _safe_int(ent_del_bid.get())
        if bid is None:
            _show_result("Введите числовой ID.", is_error=True)
            return
        if not messagebox.askyesno("Подтверждение", "Удалить бронирование?"):
            return
        try:
            ok = backend.delete_booking(bid)
            _show_result("Удалено." if ok else "Запись не найдена.")
            if ok:
                do_list_bookings()
        except Exception as ex:
            _show_result(str(ex), is_error=True)

    ttk.Button(grp_del_b, text="Удалить", command=do_delete_booking).grid(row=0, column=2, padx=(5, 0))

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)
    return frame


# --- Главное окно ---


def main():
    root = tk.Tk()
    root.title("Система бронирования")
    root.minsize(700, 550)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    notebook.add(build_users_tab(notebook), text="Пользователи")
    notebook.add(build_tables_tab(notebook), text="Столы")
    notebook.add(build_bookings_tab(notebook), text="Бронирования")

    root.mainloop()


if __name__ == "__main__":
    main()
