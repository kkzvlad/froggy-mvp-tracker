import os
import sqlite3
from datetime import datetime

DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/froggy.db")


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mvp_timers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            channel_id TEXT,
            mvp_name TEXT NOT NULL,
            map_name TEXT NOT NULL,
            killed_at TEXT NOT NULL,
            respawn_start TEXT NOT NULL,
            respawn_end TEXT NOT NULL,
            image TEXT,
            notified_10min INTEGER DEFAULT 0,
            notified_spawn INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        conn.commit()


def create_or_update_timer(
    guild_id,
    channel_id,
    mvp_name,
    map_name,
    killed_at,
    respawn_start,
    respawn_end,
    image
):
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id FROM mvp_timers
        WHERE guild_id = ? AND mvp_name = ? AND map_name = ?
        """, (str(guild_id), mvp_name, map_name))

        row = cursor.fetchone()

        if row:
            timer_id = row[0]

            cursor.execute("""
            UPDATE mvp_timers
            SET
                channel_id = ?,
                killed_at = ?,
                respawn_start = ?,
                respawn_end = ?,
                image = ?,
                notified_10min = 0,
                notified_spawn = 0,
                updated_at = ?
            WHERE id = ?
            """, (
                str(channel_id),
                killed_at.isoformat(),
                respawn_start.isoformat(),
                respawn_end.isoformat(),
                image,
                now,
                timer_id
            ))

            conn.commit()
            return timer_id, True

        cursor.execute("""
        INSERT INTO mvp_timers (
            guild_id,
            channel_id,
            mvp_name,
            map_name,
            killed_at,
            respawn_start,
            respawn_end,
            image,
            notified_10min,
            notified_spawn,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
        """, (
            str(guild_id),
            str(channel_id),
            mvp_name,
            map_name,
            killed_at.isoformat(),
            respawn_start.isoformat(),
            respawn_end.isoformat(),
            image,
            now,
            now
        ))

        conn.commit()
        return cursor.lastrowid, False


def get_active_timers(guild_id=None):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if guild_id:
            cursor.execute("""
            SELECT * FROM mvp_timers
            WHERE guild_id = ?
            ORDER BY respawn_start ASC
            """, (str(guild_id),))
        else:
            cursor.execute("""
            SELECT * FROM mvp_timers
            ORDER BY respawn_start ASC
            """)

        return [dict(row) for row in cursor.fetchall()]


def delete_timer(guild_id, mvp_name, map_name=None):
    with get_connection() as conn:
        cursor = conn.cursor()

        if map_name:
            cursor.execute("""
            DELETE FROM mvp_timers
            WHERE guild_id = ? AND mvp_name = ? AND map_name = ?
            """, (str(guild_id), mvp_name, map_name))
        else:
            cursor.execute("""
            DELETE FROM mvp_timers
            WHERE guild_id = ? AND mvp_name = ?
            """, (str(guild_id), mvp_name))

        conn.commit()
        return cursor.rowcount


def update_notification_flag(timer_id, flag_name):
    if flag_name not in ["notified_10min", "notified_spawn"]:
        raise ValueError("Invalid notification flag")

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
        UPDATE mvp_timers
        SET {flag_name} = 1, updated_at = ?
        WHERE id = ?
        """, (now, timer_id))

        conn.commit()

def get_timer_by_name(guild_id, mvp_name):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM mvp_timers
        WHERE guild_id = ? AND mvp_name = ?
        LIMIT 1
        """, (str(guild_id), mvp_name))

        row = cursor.fetchone()

        if row:
            return dict(row)

        return None