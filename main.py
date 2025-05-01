from fastapi import FastAPI, Query
from datetime import datetime
import pyodbc
import os

app = FastAPI()

# Kết nối database bằng biến môi trường
server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")
username = os.getenv("SQL_USERNAME")
password = os.getenv("SQL_PASSWORD")

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password}"
)

@app.get("/ahi")
def get_ahi(start: str = Query(...), end: str = Query(...)):
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
        SELECT COUNT(*) FROM snore_events
        WHERE event_type = 'apnea'
        AND timestamp BETWEEN ? AND ?
        """
        cursor.execute(query, (start_dt, end_dt))
        apnea_count = cursor.fetchone()[0]
        hours = (end_dt - start_dt).total_seconds() / 3600
        ahi = apnea_count / hours if hours > 0 else 0

        if ahi < 5:
            status = "Normal"
        elif ahi < 15:
            status = "Mild"
        elif ahi < 30:
            status = "Moderate"
        else:
            status = "Severe"

        return {"ahi": round(ahi, 2), "status": status}
    except Exception as e:
        return {"error": str(e)}

