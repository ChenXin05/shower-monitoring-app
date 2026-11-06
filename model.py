import sqlite3
from datetime import datetime, timedelta
import numpy as np

DB_NAME = "shower_monitor.db"


class DatabaseManager:
    """Data Layer: SQLite 3NF Relational Database (Strictly matching Figure 4.3 ERD)"""

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. USER Table (ERD Figure 4.3)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS USER (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    age TEXT NOT NULL,
                    health_conditions TEXT NOT NULL,
                    target_duration REAL NOT NULL
                )
            """)
            # 2. SHOWER_SESSION Table (ERD Figure 4.3)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS SHOWER_SESSION (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    water_temp REAL NOT NULL,
                    usage_level INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE
                )
            """)
            # 3. RECOMMENDATION Table (ERD Figure 4.3)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RECOMMENDATION (
                    rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    advice_text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES SHOWER_SESSION(session_id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            self._seed_initial_data()

    def _seed_initial_data(self):
        """Seed default User #1 and the 6 history sessions from Figure 4.7"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM USER")
            if cursor.fetchone()["cnt"] == 0:
                cursor.execute(
                    "INSERT INTO USER (age, health_conditions, target_duration) VALUES (?, ?, ?)",
                    ("28", "None", 10.0),
                )
                user_id = cursor.lastrowid

                now = datetime.now()
                seed_sessions = [
                    (
                        10.0,
                        38.0,
                        62,
                        (now - timedelta(days=3)).strftime("%Y-%m-%d 08:00:00"),
                        "Right at the recommended limit. Good thermal and water balance.",
                        "Good",
                    ),
                    (
                        16.0,
                        41.0,
                        100,
                        (now - timedelta(days=2)).strftime("%Y-%m-%d 06:50:00"),
                        "Extended hot shower may dry your skin and elevate heart rate.",
                        "Warning",
                    ),
                    (
                        6.0,
                        36.0,
                        38,
                        (now - timedelta(days=2)).strftime("%Y-%m-%d 21:30:00"),
                        "Short and gentle — great for your skin barrier and water conservation.",
                        "Good",
                    ),
                    (
                        9.0,
                        37.0,
                        56,
                        (now - timedelta(days=1)).strftime("%Y-%m-%d 07:05:00"),
                        "Well within healthy dermatological and eco range.",
                        "Good",
                    ),
                    (
                        14.0,
                        42.0,
                        88,
                        (now - timedelta(days=1)).strftime("%Y-%m-%d 20:15:00"),
                        "Too long and too hot for skin comfort; high thermal stress risk.",
                        "Warning",
                    ),
                    (
                        8.1,
                        38.0,
                        62,
                        now.strftime("%Y-%m-%d 07:42:00"),
                        "Ideal duration and temperature. Keep it under 10 minutes to protect natural skin oils.",
                        "Good",
                    ),
                ]
                for dur, temp, usage, ts, advice, cat in seed_sessions:
                    cursor.execute(
                        """
                        INSERT INTO SHOWER_SESSION (user_id, duration, water_temp, usage_level, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (user_id, dur, temp, usage, ts),
                    )
                    sess_id = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO RECOMMENDATION (session_id, advice_text, category)
                        VALUES (?, ?, ?)
                    """,
                        (sess_id, advice, cat),
                    )
                conn.commit()

    def get_all_users(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM USER ORDER BY user_id ASC")
            return [dict(row) for row in cur.fetchall()]

    def get_user(self, user_id=1):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM USER WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            cur.execute("SELECT * FROM USER ORDER BY user_id ASC LIMIT 1")
            return dict(cur.fetchone())

    def create_user(self, age, health_conditions, target_duration):
        """Sign-Up: Creates a new anonymous local user profile in USER table (ERD Fig 4.3)"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO USER (age, health_conditions, target_duration)
                VALUES (?, ?, ?)
            """,
                (str(age), health_conditions, float(target_duration)),
            )
            conn.commit()
            return cur.lastrowid

    def update_user(self, user_id, age, health_conditions, target_duration):
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE USER
                SET age = ?, health_conditions = ?, target_duration = ?
                WHERE user_id = ?
            """,
                (str(age), health_conditions, float(target_duration), user_id),
            )
            conn.commit()

    def insert_session_and_recommendations(
        self, user_id, duration, water_temp, usage_level, recommendations, timestamp=None
    ):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO SHOWER_SESSION (user_id, duration, water_temp, usage_level, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, float(duration), float(water_temp), int(usage_level), timestamp),
            )
            session_id = cur.lastrowid
            for rec in recommendations:
                cur.execute(
                    """
                    INSERT INTO RECOMMENDATION (session_id, advice_text, category)
                    VALUES (?, ?, ?)
                """,
                    (session_id, rec["advice_text"], rec["category"]),
                )
            conn.commit()
            return session_id

    def get_user_sessions_with_recommendations(self, user_id=1):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.session_id, s.user_id, s.duration, s.water_temp, s.usage_level, s.timestamp,
                       GROUP_CONCAT(r.advice_text, ' ') AS advice_text,
                       CASE WHEN SUM(CASE WHEN r.category = 'Warning' THEN 1 ELSE 0 END) > 0
                            THEN 'Warning' ELSE 'Good' END AS status_badge
                FROM SHOWER_SESSION s
                LEFT JOIN RECOMMENDATION r ON s.session_id = r.session_id
                WHERE s.user_id = ?
                GROUP BY s.session_id
                ORDER BY s.timestamp DESC, s.session_id DESC
            """,
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_table_dump(self, table_name):
        """Helper to view raw SQLite tables directly in the UI"""
        allowed = {"USER", "SHOWER_SESSION", "RECOMMENDATION"}
        if table_name not in allowed:
            return []
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table_name}")
            return [dict(row) for row in cur.fetchall()]

    def clear_and_reset(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM RECOMMENDATION")
            conn.execute("DELETE FROM SHOWER_SESSION")
            conn.execute("DELETE FROM USER")
            conn.execute("DELETE FROM sqlite_sequence")
            conn.commit()
        self._seed_initial_data()


class MamdaniFuzzyEngine:
    """Logic Layer: Mamdani Fuzzy Inference System (FIS) & Centroid Defuzzification"""

    @staticmethod
    def trapmf(x, a, b, c, d):
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)
        if b > a:
            idx = (x > a) & (x < b)
            y[idx] = (x[idx] - a) / (b - a)
        y[(x >= b) & (x <= c)] = 1.0
        if d > c:
            idx = (x > c) & (x < d)
            y[idx] = (d - x[idx]) / (d - c)
        return float(y) if y.ndim == 0 else y

    @staticmethod
    def trimf(x, a, b, c):
        return MamdaniFuzzyEngine.trapmf(x, a, b, b, c)

    def fuzzify_duration(self, duration):
        d = max(0.0, min(float(duration), 30.0))
        return {
            "Short": self.trapmf(d, 0.0, 0.0, 4.5, 6.5),
            "Optimal": self.trimf(d, 4.5, 7.5, 10.5),
            "Prolonged": self.trapmf(d, 9.0, 11.5, 30.0, 30.0),
        }

    def fuzzify_temperature(self, temp):
        t = max(20.0, min(float(temp), 50.0))
        return {
            "Low": self.trapmf(t, 20.0, 20.0, 34.0, 36.8),
            "Moderate": self.trimf(t, 35.5, 38.0, 39.8),
            "High": self.trapmf(t, 39.0, 40.2, 50.0, 50.0),
        }

    def fuzzify_usage(self, usage_pct):
        u = max(0.0, min(float(usage_pct), 150.0))
        return {
            "Low": self.trapmf(u, 0.0, 0.0, 40.0, 60.0),
            "Moderate": self.trimf(u, 45.0, 68.0, 90.0),
            "High": self.trapmf(u, 80.0, 100.0, 150.0, 150.0),
        }

    def evaluate(self, duration, water_temp, usage_level):
        dur_mf = self.fuzzify_duration(duration)
        temp_mf = self.fuzzify_temperature(water_temp)
        use_mf = self.fuzzify_usage(usage_level)

        r_low_1 = min(dur_mf["Short"], temp_mf["Low"])
        r_low_2 = min(dur_mf["Short"], temp_mf["Moderate"])
        r_low_3 = min(dur_mf["Optimal"], temp_mf["Low"])
        r_low_4 = min(dur_mf["Optimal"], temp_mf["Moderate"])
        firing_low = max(r_low_1, r_low_2, r_low_3, r_low_4)

        r_mod_1 = min(dur_mf["Short"], temp_mf["High"])
        r_mod_2 = min(dur_mf["Prolonged"], temp_mf["Low"])
        firing_mod = max(r_mod_1, r_mod_2)

        r_high_1 = min(dur_mf["Optimal"], temp_mf["High"])
        r_high_2 = min(dur_mf["Prolonged"], temp_mf["Moderate"])
        r_high_3 = min(dur_mf["Prolonged"], temp_mf["High"])
        r_high_4 = use_mf["High"]
        firing_high = max(r_high_1, r_high_2, r_high_3, r_high_4)

        x_risk = np.linspace(0, 100, 501)
        mf_risk_low = self.trapmf(x_risk, 0, 0, 25, 45)
        mf_risk_mod = self.trimf(x_risk, 30, 50, 70)
        mf_risk_high = self.trapmf(x_risk, 55, 75, 100, 100)

        agg_low = np.minimum(firing_low, mf_risk_low)
        agg_mod = np.minimum(firing_mod, mf_risk_mod)
        agg_high = np.minimum(firing_high, mf_risk_high)
        aggregated = np.maximum.reduce([agg_low, agg_mod, agg_high])

        denom = np.sum(aggregated)
        centroid_score = float(np.sum(x_risk * aggregated) / denom) if denom > 0 else 20.0

        dom_duration = max(dur_mf, key=dur_mf.get)
        dom_temp = max(temp_mf, key=temp_mf.get)
        dom_usage = max(use_mf, key=use_mf.get)

        temp_display_map = {"Low": "Cool / Lukewarm", "Moderate": "Warm", "High": "Hot"}
        overall_status = (
            "Warning"
            if (centroid_score >= 50.0 or duration > 10.5 or water_temp >= 40.0)
            else "Good"
        )

        return {
            "duration_mf": dur_mf,
            "temp_mf": temp_mf,
            "usage_mf": use_mf,
            "dom_duration": dom_duration,
            "dom_temp": dom_temp,
            "dom_temp_label": temp_display_map[dom_temp],
            "dom_usage": dom_usage,
            "centroid_score": round(centroid_score, 2),
            "overall_status": overall_status,
            "firing_strengths": {
                "Low Risk": round(firing_low, 3),
                "Moderate Risk": round(firing_mod, 3),
                "High Risk": round(firing_high, 3),
            },
        }