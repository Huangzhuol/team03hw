# server/data_schema.py
from pydantic import BaseModel, Field
from typing import Literal
from typing import Union

class BasicInfoModel(BaseModel):
    dataset: Literal[
        "attention_summary",
        "decoder_variable_importances",
        "encoder_variable_importances",
        "static_variable_importances"
    ] = Field(..., description="data source")
    key: Union[str, int]       
    value: float