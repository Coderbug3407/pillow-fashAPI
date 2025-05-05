from fastapi import FastAPI, Query
from datetime import datetime
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
def get_ahi_with_stored_proc(start_date: str = Query(...), end_date: str = Query(...)):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Chuyển kiểu dữ liệu
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Gọi stored procedure
        cursor.execute("EXEC GetAHIData ?, ?", start_dt, end_dt)

        # Kết quả 1: AHI và status
        row = cursor.fetchone()
        ahi = row.ahi
        status = row.status

        # Di chuyển tới kết quả thứ 2: dữ liệu
        cursor.nextset()
        data_rows = cursor.fetchall()

        data = []
        for row in data_rows:
            data.append({
                "deviceId": row.deviceId,
                "snoringBegintime": row.snoringBegintime.isoformat(),
                "intensity": row.intensity,
                "intervention": json.loads(row.intervention) if isinstance(row.intervention, str) else row.intervention,
                "snoringEndtime": row.snoringEndtime.isoformat()
            })

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
