# Snoring API – FastAPI with Azure Cosmos DB

This is a small FastAPI project I wrote to query and analyze snoring data stored in Azure Cosmos DB. Mainly used for a sleep monitoring system.

![image](https://github.com/user-attachments/assets/41ba2212-ce9a-4f20-a578-834ca43c49ba)


It includes two endpoints:
- `/ahi`: calculates the Apnea–Hypopnea Index (AHI) based on snoring events.
- `/snoring_data`: returns raw snoring records between two timestamps.

## Tech Stack
- Python 3.9+
- FastAPI
- Azure Cosmos DB (NoSQL)
- dateutil for datetime parsing

## Getting Started

### 1. Install dependencies
Make sure you're in a virtual environment:
```bash
pip install -r requirements.txt
```

### 2. Set environment variables
You'll need to provide the following:
```
COSMOS_ENDPOINT=<your-cosmos-endpoint>
COSMOS_KEY=<your-cosmos-key>
COSMOS_DATABASE=<your-database-name>
COSMOS_CONTAINER=<your-container-name>
```
You can export them manually or use a .env file if you're using a package like python-dotenv.

### 3. Run the app
```bash
uvicorn main:app --reload
```
Visit: http://localhost:8000/docs to test the endpoints with Swagger UI.

## API Endpoints

### GET /ahi
Calculates AHI using the number of snoring events and the total hours between start_date and end_date.

**Query Parameters:**
- start_date: string – format YYYY-MM-DD HH:MM
- end_date: string – format YYYY-MM-DD HH:MM

**Response:**
```json
{
  "data": [
    {
      "ahi": 2.85
    }
  ]
}
```

### GET /snoring_data
Returns detailed snoring event data between start_date and end_date.

**Query Parameters:**
- start_date: ISO 8601 string
- end_date: ISO 8601 string

**Response:**
```json
{
  "data": [
    {
      "id": "event1",
      "deviceId": "esp32-001",
      "snoringBegintime": "2025-05-15T01:12:00",
      "intensity": 5,
      "intervention": false,
      "snoringEndtime": "2025-05-15T01:12:40"
    }
  ]
}
```


## Notes
- AHI is just calculated as snore_count / sleep_hours, not a clinical measure.
- Make sure your Cosmos DB container is configured with a proper partition key (/id or similar).
- Timezones are assumed to be consistent (you can adjust that if needed).
- Basic error handling is included.
