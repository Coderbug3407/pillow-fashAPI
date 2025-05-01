from fastapi import FastAPI, Query
from datetime import datetime
import pyodbc
import os
import json

app = FastAPI()

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
def get_ahi_with_data(start: str = Query(...), end: str = Query(...)):
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
        SELECT deviceId, timestamp, snoringLevel, intervention, snoringEndtime
        FROM snore_events
        WHERE timestamp BETWEEN ? AND ?
        """
        cursor.execute(query, (start_dt, end_dt))
        rows = cursor.fetchall()

        apnea_count = 0
        data = []

        for row in rows:
            start_time = row.timestamp
            end_time = row.snoringEndtime
            duration = (end_time - start_time).total_seconds()

            if duration >= 10:  # giả định >10s là apnea
                apnea_count += 1

            data.append({
                "deviceId": row.deviceId,
                "timestamp": start_time.isoformat(),
                "snoringLevel": row.snoringLevel,
                "intervention": row.intervention,  # raw JSON string
                "snoringEndtime": end_time.isoformat()
            })

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

        return {
            "ahi": round(ahi, 2),
            "status": status,
            "data": data
        }
    except Exception as e:
        return {"error": str(e)}
