import sqlite3
import pandas as pd

from src.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Establish a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def load_data() -> pd.DataFrame:
    query = """
        SELECT
            l.motor_id,
            l.timestamp,
            l.rotacao_rpm,
            l.vibracao_mm_s,
            l.temperatura_c,
            l.corrente_a,
            l.falha,
            m.fabricante,
            m.modelo,
            m.potencia_kw
        FROM leituras l
        JOIN motores m ON l.motor_id = m.motor_id
        ORDER BY l.motor_id, l.timestamp
    """
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, parse_dates=["timestamp"])
    return df

def load_failure_types() -> dict:
    query = "SELECT codigo, nome FROM tipos_falha ORDER BY codigo"
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)
    return dict(zip(df["codigo"], df["nome"]))