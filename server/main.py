# server/main.py
from fastapi import FastAPI, HTTPException, Query
from data_schema import BasicInfoModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict

from data_schema import BasicInfoModel, SalaryRecordModel, LocationOverview

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
    limit: int = Query(100, ge=1, le=2000),
):
    cursor = salary_coll.find({"job_title": job_title}, limit=limit)
    docs   = [SalaryRecordModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(404, f"No salary records for job_title={job_title}")
    return docs

@app.get("/salaries/{job_title}/experience_levels", response_model=Dict[str, int])
async def experience_level_stats(job_title: str):
    pipeline = [
        {"$match": {"job_title": job_title}},
        {"$group": {"_id": "$experience_level", "count": {"$sum": 1}}},
    ]
    cursor = salary_coll.aggregate(pipeline)

    stats: Dict[str, int] = {}
    async for doc in cursor:
        stats[doc["_id"]] = doc["count"]

    if not stats:
        raise HTTPException(404, f"No salary records for job_title={job_title}")

    return stats


@app.get("/salaries/{job_title}/{experience_level}", response_model=List[SalaryRecordModel])
async def salaries_by_title_level(job_title: str, experience_level: str):
    query = {"job_title": job_title, "experience_level": experience_level}
    cursor = salary_coll.find(query)
    docs = [SalaryRecordModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(
            404,
            f"No salary records for job_title='{job_title}' & experience_level='{experience_level}'",
        )
    return docs


@app.get("/salary_location", response_model=LocationOverview)
async def location_overview():
    pipeline = [
        {"$group": {"_id": "$company_location", "count": {"$sum": 1}}},
        {"$sort":  {"count": -1}},
    ]
    cursor = salary_coll.aggregate(pipeline)
    loc_dict = {doc["_id"]: doc["count"] async for doc in cursor}

    if not loc_dict:
        raise HTTPException(404, "No salary records in database.")

    return {
        "total_locations": len(loc_dict),
        "locations": loc_dict,
    }

@app.get("/salary_location/{company_location}", response_model=List[SalaryRecordModel])
async def salaries_by_location(company_location: str):
    cursor = (
        salary_coll
        .find({"company_location": company_location})
    )
    docs = [SalaryRecordModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(404, f"No salary records for company_location='{company_location}'")
    return docs

@app.get(
    "/salary_location/{company_location}/{job_title}",
    response_model=List[SalaryRecordModel],
)
async def salaries_by_location_title(company_location: str, job_title: str):
    query = {
        "company_location": company_location,
        "job_title": job_title,
    }
    cursor = salary_coll.find(query)
    docs = [SalaryRecordModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(
            404,
            f"No salary records for company_location='{company_location}' & job_title='{job_title}'",
        )
    return docs