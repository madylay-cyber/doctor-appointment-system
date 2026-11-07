import sqlite3
from typing import Optional
from app.models.schemas import UserModel
from app.core.config import settings

class UserRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        if settings.db_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, fio, phone, email, oms_policy, role_id FROM Users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            if row:
                return UserModel(*row)
            return None

    def get_by_oms(self, oms_policy: str) -> Optional[UserModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, fio, phone, email, oms_policy, role_id FROM Users WHERE oms_policy = ?;", (oms_policy,))
            row = cursor.fetchone()
            if row:
                return UserModel(*row)
            return None

    def update_contacts(self, user_id: int, phone: str, email: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET phone = ?, email = ? WHERE id = ?;", (phone, email, user_id))
            conn.commit()
            return cursor.rowcount > 0
