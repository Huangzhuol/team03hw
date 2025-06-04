# server/data_schema.py
from pydantic import BaseModel, Field
from typing import Literal, Union, Dict

class BasicInfoModel(BaseModel):
    dataset: Literal[
        "attention_summary",
        "decoder_variable_importances",
        "encoder_variable_importances",
        "static_variable_importances"
    ] = Field(..., description="data source")
    key: Union[str, int]       
    value: float

class SalaryRecordModel(BaseModel):
    job_title:          str
    employment_type:    str
    experience_level:   str
    expertise_level:    str
    salary:             int
    salary_currency:    str
    company_location:   str
    salary_in_usd:      int
    employee_residence: str
    company_size:       str
    year:               int


class LocationOverview(BaseModel):
    total_locations: int
    locations: Dict[str, int]


class PredictionModel(BaseModel):
    job_title: str
    experience_level: str
    year: int
    predicted_salary_usd: float