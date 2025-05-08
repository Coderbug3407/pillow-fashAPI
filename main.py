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
        # Parse thời gian đầu và cuối
        start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

        # Tính tổng thời gian ngủ theo giờ
        total_sleep_hours = (end_dt - start_dt).total_seconds() / 3600

        if total_sleep_hours <= 0:
            return {"error": "End date must be after start date."}

        # Query để đếm số lần ngáy
        query = f"""
            SELECT VALUE COUNT(1) 
            FROM c 
            WHERE c.snoringBegintime >= "{start_dt.isoformat()}" AND c.snoringBegintime <= "{end_dt.isoformat()}"
        """
        ahi_results = list(container.query_items(query=query, enable_cross_partition_query=True))
        snore_count = ahi_results[0] if ahi_results else 0

        # Tính AHI
        ahi = snore_count / total_sleep_hours

        return {
            "data": [
                {
                    "ahi": round(ahi, 2)
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