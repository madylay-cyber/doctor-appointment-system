import sqlite3
from typing import Optional, List, Dict, Any
from app.models.schemas import AppointmentModel, CommentModel
from app.core.config import settings

class AppointmentRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        if settings.db_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def check_slot_conflict(self, doctor_id: int, datetime_slot: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM Requests WHERE doctor_id = ? AND datetime_slot = ? AND status_id != 5;", 
                (doctor_id, datetime_slot)
            )
            return cursor.fetchone() is not None

    def create_appointment(self, patient_id: int, doctor_id: int, category_id: int, datetime_slot: str) -> AppointmentModel:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Requests (patient_id, doctor_id, category_id, status_id, datetime_slot) VALUES (?, ?, ?, 2, ?);",
                (patient_id, doctor_id, category_id, datetime_slot)
            )
            conn.commit()
            return AppointmentModel(cursor.lastrowid, patient_id, doctor_id, category_id, 2, datetime_slot)

    def block_doctor_slots(self, doctor_id: int, start_date: str, end_date: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Requests SET status_id = 5 WHERE doctor_id = ? AND datetime_slot BETWEEN ? AND ?;",
                (doctor_id, f"{start_date} 00:00", f"{end_date} 23:59")
            )
            conn.commit()
            return cursor.rowcount

    def get_medical_history(self, patient_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id, d.fio, r.datetime_slot, c.text_content 
                FROM Requests r
                JOIN Users d ON r.doctor_id = d.id
                LEFT JOIN Comments c ON c.request_id = r.id AND c.author_id = r.doctor_id
                WHERE r.patient_id = ? AND r.status_id = 4;
            """, (patient_id,))
            return [{"appointment_id": row[0], "doctor": row[1], "date": row[2], "conclusion": row[3]} for row in cursor.fetchall()]

    def add_comment(self, request_id: int, author_id: int, text: str, timestamp: str) -> CommentModel:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Comments (request_id, author_id, text_content, created_at) VALUES (?, ?, ?, ?);",
                (request_id, author_id, text, timestamp)
            )
            conn.commit()
            return CommentModel(cursor.lastrowid, request_id, author_id, text, timestamp)
