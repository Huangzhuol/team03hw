# server/main.py
from fastapi import FastAPI, HTTPException
from data_schema import BasicInfoModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

from data_schema import BasicInfoModel

MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "team03hw"
COLL_NAME = "tft_basic_info"

app = FastAPI(title="TFT Basic Info API")

client = AsyncIOMotorClient(MONGO_URI)
coll   = client[DB_NAME][COLL_NAME]

@app.get("/records", response_model=List[BasicInfoModel])
async def list_all(limit: int = 100):
    cursor = coll.find({}, limit=limit)
    return [BasicInfoModel(**doc) async for doc in cursor]

@app.get("/records/{dataset}", response_model=List[BasicInfoModel])
async def list_by_dataset(dataset: str, limit: int = 100):
    cursor = coll.find({"dataset": dataset}, limit=limit)
    docs = [BasicInfoModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(404, f"No records in dataset={dataset}")
    return docs

@app.get("/records/{dataset}/{key}", response_model=BasicInfoModel)
async def get_single(dataset: str, key: str):
    doc = await coll.find_one({"dataset": dataset, "key": key})
    if not doc:
        raise HTTPException(404, "Record not found")
    return BasicInfoModel(**doc)
