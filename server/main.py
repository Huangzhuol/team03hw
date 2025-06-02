# server/main.py
from fastapi import FastAPI, HTTPException, Query
from data_schema import BasicInfoModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional

from data_schema import BasicInfoModel, SalaryRecordModel

MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "team03hw"
COLL_NAME = "tft_basic_info"

app = FastAPI(title="TFT Basic Info API")

client = AsyncIOMotorClient(MONGO_URI)
coll   = client[DB_NAME][COLL_NAME]
salary_coll = client[DB_NAME]["salaries_filtered"]

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

@app.get("/salaries", response_model=List[SalaryRecordModel])
async def list_salaries(
    limit: int = Query(100, ge=1, le=1000),
    job_title: Optional[str] = None,
):
    query  = {"job_title": job_title} if job_title else {}
    cursor = salary_coll.find(query, limit=limit)
    return [SalaryRecordModel(**doc) async for doc in cursor]


@app.get("/salaries/{job_title}", response_model=List[SalaryRecordModel])
async def list_salaries_by_title(
    job_title: str,
    limit: int = Query(100, ge=1, le=1000),
):
    cursor = salary_coll.find({"job_title": job_title}, limit=limit)
    docs   = [SalaryRecordModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(404, f"No salary records for job_title={job_title}")
    return docs
