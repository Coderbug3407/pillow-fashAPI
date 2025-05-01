from fastapi import FastAPI, Query
from datetime import datetime
import pyodbc
import os

app = FastAPI()

# Biến môi trường kết nối SQL Server
server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")
username = os.getenv("SQL_USERNAME")
password = os.getenv("SQL_PASSWORD")

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password}"
)

@app.get("/data")
def get_snore_data(start: str = Query(...), end: str = Query(...)):
    try:
        # Parse ISO time
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        # Kết nối DB
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Truy vấn tất cả dữ liệu trong khoảng thời gian
        query = """
        SELECT deviceId, timestamp, snoringLevel, intervention, snoringEndtime
        FROM snore_events
        WHERE timestamp BETWEEN ? AND ?
        """
        cursor.execute(query, (start_dt, end_dt))
        rows = cursor.fetchall()

        result = []
        apnea_count = 0

        for row in rows:
            device_id, timestamp, snoring_level, intervention, snoring_endtime = row

            # Chuyển timestamp -> datetime để tính AHI
            try:
                start_time = datetime.fromisoformat(str(timestamp))
                end_time = datetime.fromisoformat(str(snoring_endtime))
            except Exception:
                continue  # bỏ qua nếu định dạng sai

            duration = (end_time - start_time).total_seconds()

            # Đếm nếu thời gian ngáy >= 10 giây → coi như 1 đợt apnea
            if duration >= 10:
                apnea_count += 1

            result.append({
                "deviceId": device_id,
                "timestamp": str(timestamp),
                "snoringLevel": snoring_level,
                "intervention": intervention,
                "snoringEndtime": str(snoring_endtime)
            })

        # Tính AHI
        hours = (end_dt - start_dt).total_seconds() / 3600
        ahi = apnea_count / hours if hours > 0 else 0

        # Phân loại mức độ
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
            "data": result
        }

    except Exception as e:
        return {"error": str(e)}
