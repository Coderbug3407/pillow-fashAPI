from fastapi import FastAPI, Query
from datetime import datetime
import os
import json
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dateutil import parser
app = FastAPI()

# DB connection
cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
cosmos_key = os.getenv("COSMOS_KEY")
cosmos_database = os.getenv("COSMOS_DATABASE")
cosmos_container = os.getenv("COSMOS_CONTAINER")

# Cosmos DB client setup
client = CosmosClient(cosmos_endpoint, cosmos_key)
database = client.get_database_client(cosmos_database)
container = database.get_container_client(cosmos_container)

@app.get("/ahi")
def get_ahi_with_stored_proc(start_date: str = Query(...), end_date: str = Query(...)):
    try:
        # Chuyển kiểu dữ liệu
        start_dt = parser.parse(start_date)
        end_dt = parser.parse(end_date)

        # Tính tổng số giờ ngủ
        total_hours = (end_dt - start_dt).total_seconds() / 3600.0
        if total_hours == 0:
            return {"error": "Thời gian ngủ phải lớn hơn 0"}

        # Query Cosmos DB để đếm số sự kiện ngáy
        query = f"""
            SELECT VALUE COUNT(1) 
            FROM c 
            WHERE c.snoringBegintime >= "{start_dt.isoformat()}" AND c.snoringBegintime <= "{end_dt.isoformat()}"
        """
        count_result = list(container.query_items(query=query, enable_cross_partition_query=True))

        # Số sự kiện ngáy
        total_snoring_events = count_result[0] if count_result else 0

        # Tính AHI
        ahi = total_snoring_events / total_hours

        return {
            "data": [
                {
                    "ahi": round(ahi, 2),
                    "total_events": total_snoring_events,
                    "duration_hours": round(total_hours, 2)
                }
            ]
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/snoring_data")
def get_snoring_data(start_date: str = Query(...), end_date: str = Query(...)):
    try:
        # Chuyển kiểu dữ liệu

        start_dt = parser.parse(start_date)
        end_dt = parser.parse(end_date)

        # Query Cosmos DB để lấy dữ liệu ngáy
        query = f"""
            SELECT c.id, c.deviceId, c.snoringBegintime, c.intensity, c.intervention, c.snoringEndtime
            FROM c 
            WHERE c.snoringBegintime >= "{start_dt.isoformat()}" AND c.snoringBegintime <= "{end_dt.isoformat()}"
        """

        # Thực hiện truy vấn để lấy các bản ghi
        data_rows = list(container.query_items(query=query, enable_cross_partition_query=True))

        data = []
        for row in data_rows:
            data.append({
                "id": row["id"],
                "deviceId": row["deviceId"],
                "snoringBegintime": row["snoringBegintime"],
                "intensity": row["intensity"],
                "intervention": row["intervention"],
                "snoringEndtime": row["snoringEndtime"]
            })

        return {
            "data": data
        }

    except Exception as e:
        return {"error": str(e)}
