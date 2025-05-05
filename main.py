from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pyodbc, os, json

app = FastAPI()

# DB connection
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
def get_ahi_with_data(start_date: str = Query(None), end_date: str = Query(None)):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

            query = """
            SELECT deviceId, snoringBegintime, intensity, intervention, snoringEndtime
            FROM SnoreLogs
            WHERE snoringBegintime BETWEEN ? AND ?
            """
            cursor.execute(query, (start_dt, end_dt))
        else:
            query = """
            SELECT deviceId, snoringBegintime, intensity, intervention, snoringEndtime
            FROM SnoreLogs
            """
            cursor.execute(query)

        rows = cursor.fetchall()
        apnea_count = 0
        data = []

        for row in rows:
            start_time = row.snoringBegintime
            end_time = row.snoringEndtime
            duration = (end_time - start_time).total_seconds()

            if duration >= 10:
                apnea_count += 1

            data.append({
                "deviceId": row.deviceId,
                "snoringBegintime": start_time.isoformat(),
                "intensity": row.intensity,
                "intervention": json.loads(row.intervention) if isinstance(row.intervention, str) else row.intervention,
                "snoringEndtime": end_time.isoformat()
            })

        if start_date and end_date:
            hours = (end_dt - start_dt).total_seconds() / 3600
        else:
            timestamps = [row.snoringBegintime for row in rows]
            if len(timestamps) < 2:
                hours = 1
            else:
                hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600

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

    finally:
        cursor.close()
        conn.close()
