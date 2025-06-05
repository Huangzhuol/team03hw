# server/main.py
from fastapi import FastAPI, HTTPException, Query
from data_schema import BasicInfoModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from data_schema import BasicInfoModel, SalaryRecordModel, LocationOverview, PredictionModel

MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "team03hw"
COLL_NAME = "tft_basic_info"

app = FastAPI(title="TFT Basic Info API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient(MONGO_URI)
coll   = client[DB_NAME][COLL_NAME]
salary_coll = client[DB_NAME]["salaries_filtered"]
predictions_coll = client[DB_NAME]["tft_predictions"]

# List all basic info records, with optional limit
@app.get("/records", response_model=List[BasicInfoModel])
async def list_all(limit: int = 100):
    cursor = coll.find({}, limit=limit)
    return [BasicInfoModel(**doc) async for doc in cursor]

# List records by dataset name
@app.get("/records/{dataset}", response_model=List[BasicInfoModel])
async def list_by_dataset(dataset: str, limit: int = 100):
    cursor = coll.find({"dataset": dataset}, limit=limit)
    docs = [BasicInfoModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(404, f"No records in dataset={dataset}")
    return docs

# Get a single record by dataset and key
@app.get("/records/{dataset}/{key}", response_model=BasicInfoModel)
async def get_single(dataset: str, key: str):
    doc = await coll.find_one({"dataset": dataset, "key": key})
    if not doc:
        raise HTTPException(404, "Record not found")
    return BasicInfoModel(**doc)

# List salary records, optionally filtered by job title
@app.get("/salaries", response_model=List[SalaryRecordModel])
async def list_salaries(
    limit: int = Query(100, ge=1, le=2000),
    job_title: Optional[str] = None,
):
    query  = {"job_title": job_title} if job_title else {}
    cursor = salary_coll.find(query, limit=limit)
    return [SalaryRecordModel(**doc) async for doc in cursor]

# List salaries for a specific job title
@app.get("/salaries/{job_title}", response_model=List[SalaryRecordModel])
async def list_salaries_by_title(
    job_title: str
):
    cursor = salary_coll.find({"job_title": job_title})
    docs   = [SalaryRecordModel(**doc) async for doc in cursor]
    if not docs:
        raise HTTPException(404, f"No salary records for job_title={job_title}")
    return docs

# Get counts of each experience level for a given job title
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

# List salaries by job title and experience level
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

# Get number of records per company location
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

# List salaries filtered by company location
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

# List salaries by company location and job title
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

# Get average salary per job title
@app.get("/avg_salaries", response_model=Dict[str, float])
async def average_salary_by_title():
    pipeline = [
        {"$group": {
            "_id": "$job_title",
            "avg_salary": {"$avg": "$salary_in_usd"}
        }},
        {"$sort": {"avg_salary": -1}}
    ]
    cursor = salary_coll.aggregate(pipeline)

    result: Dict[str, float] = {}
    async for doc in cursor:
        job_title = doc["_id"]
        avg_salary = round(doc["avg_salary"], 2)
        result[job_title] = avg_salary

    if not result:
        raise HTTPException(404, "No salary data found.")
    
    return JSONResponse(content=result)

# Get average salary by experience level for a job title
@app.get("/avg_salaries/{job_title}", response_model=Dict[str, float])
async def avg_salary_by_experience_level(job_title: str):
    pipeline = [
        {"$match": {"job_title": job_title}},
        {"$group": {
            "_id": "$experience_level",
            "avg_salary": {"$avg": "$salary_in_usd"}
        }},
        {"$sort": {"avg_salary": -1}}
    ]
    cursor = salary_coll.aggregate(pipeline)

    result: Dict[str, float] = {}
    async for doc in cursor:
        level = doc["_id"]
        avg_salary = round(doc["avg_salary"], 2)
        result[level] = avg_salary

    if not result:
        raise HTTPException(404, f"No salary data for job_title='{job_title}'")

    return result

# Get all TFT prediction records
@app.get(
    "/tft_predictions",
    response_model=List[PredictionModel],
)
async def get_all_tft_predictions():
    cursor = predictions_coll.find({})
    
    docs: List[PredictionModel] = []
    async for doc in cursor:
        docs.append(PredictionModel(**doc))

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="No prediction records found in 'tft_predictions'.",
        )
    return docs


# Get average salary by year and experience level for a job title (excluding 2025)
@app.get(
    "/avg_sal_by_year/{job_title}",
    response_model=Dict[int, Dict[str, float]],
)
async def avg_salary_by_year(job_title: str):
    pipeline = [
        {
            "$match": {
                "job_title": job_title,
                "year": {"$ne": 2025} 
            }
        },
        {
            "$group": {
                "_id": {
                    "year": "$year",
                    "level": "$experience_level"
                },
                "avg_salary": {"$avg": "$salary_in_usd"}
            }
        },
        {
            "$sort": {
                "_id.year": 1,
                "_id.level": 1
            }
        }
    ]
    cursor = salary_coll.aggregate(pipeline)


    temp: Dict[int, Dict[str, float]] = {}
    async for doc in cursor:
        year = doc["_id"]["year"]                 
        level = doc["_id"]["level"]                
        avg_usd = round(doc["avg_salary"], 2)     

        if year not in temp:
            temp[year] = {}
        temp[year][level] = avg_usd

    if not temp:
        raise HTTPException(
            status_code=404,
            detail=f"No salary data found for job_title='{job_title}'"
        )
    return temp

