# server/import_data.py
import pandas as pd
from pymongo import MongoClient
from pathlib import Path

from data_schema import BasicInfoModel, SalaryRecordModel

CSV_SALARIES = Path(__file__).parent.parent / "data" / "salaries.csv"
CSV_PREDICTIONS = Path(__file__).parent.parent / "result" / "TFT_Predictions.csv"
SELECTED_TITLES = {
    "Data Analyst",
    "Data Analytics Manager",
    "Data Architect",
    "Data Engineer",
    "Data Scientist",
    "Head of Data",
    "Machine Learning Engineer",
    "Machine Learning Scientist",
    "Research Scientist",
}

CSV_DIR = Path(__file__).parent.parent / "result"        
CSV_FILES = {
    "attention_summary": "attention_summary.csv",
    "decoder_variable_importances": "decoder_variable_importances.csv",
    "encoder_variable_importances": "encoder_variable_importances.csv",
    "static_variable_importances": "static_variable_importances.csv",
}
MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "team03hw"
COLL_NAME = "tft_basic_info"
client       = MongoClient(MONGO_URI)   
salary_coll = client[DB_NAME]["salaries_filtered"]
coll   = client[DB_NAME][COLL_NAME]
predictions_coll = client[DB_NAME]["tft_predictions"]


def read_and_normalize(name: str, filename: str) -> pd.DataFrame:
    df = pd.read_csv(CSV_DIR / filename)

    if name == "attention_summary":
        df = df.rename(columns={"Encoder Step": "key", "Attention Weight": "value"})
    else:
        df = df.rename(columns={"Variable": "key", "Importance (%)": "value"})

    df["dataset"] = name
    assert set(df.columns) >= {"key", "value", "dataset"}
    return df[["dataset", "key", "value"]]

def main():
    frames = [read_and_normalize(ds, fn) for ds, fn in CSV_FILES.items()]
    df_all = pd.concat(frames, ignore_index=True)
    print(f"Total rows to insert: {len(df_all)}")

    for rec in df_all.to_dict("records"):
        BasicInfoModel(**rec)

    coll.delete_many({})
    coll.insert_many(df_all.to_dict("records"))
    print(f"Inserted {coll.count_documents({})} documents into {COLL_NAME}.")


    df = pd.read_csv(CSV_SALARIES)
    df = df[df["job_title"].isin(SELECTED_TITLES)].copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    df.rename(columns={"work_year": "year"}, inplace=True)

    mapping = {"EN": "Entry", "MI": "Mid", "SE": "Senior", "EX": "Executive"}
    df["experience_level"] = df["experience_level"].map(mapping)

    required_fields = {"job_title", "experience_level", "salary_in_usd", "employee_residence", "year"}
    df = df[[col for col in df.columns if col in required_fields]]

    records = []
    for rec in df.to_dict("records"):
        validated = SalaryRecordModel(**rec)
        records.append(validated.model_dump(by_alias=True))  

    salary_coll.delete_many({})
    if records:
        salary_coll.insert_many(records)
    print(f"Inserted {salary_coll.count_documents({})} salary records into salaries_filtered.")


# predictions
if CSV_PREDICTIONS.exists():
    df_pred = pd.read_csv(CSV_PREDICTIONS)

    df_pred = df_pred.rename(columns=lambda c: c.lower().replace(" ", "_"))

    mapping = {"EN": "Entry", "MI": "Mid", "SE": "Senior", "EX": "Executive"}
    if "experience_level" in df_pred.columns:
        df_pred["experience_level"] = df_pred["experience_level"].map(mapping)

    pred_records = df_pred.to_dict("records")
    predictions_coll.delete_many({})
    if pred_records:
        predictions_coll.insert_many(pred_records)
    print(f"Inserted {predictions_coll.count_documents({})} prediction records into tft_predictions.")
else:
    print(f"Warning: {CSV_PREDICTIONS} not found, skip importing predictions.")



if __name__ == "__main__":
    main()
