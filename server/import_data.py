# server/import_data.py
import pandas as pd
from pymongo import MongoClient
from pathlib import Path

from data_schema import BasicInfoModel, SalaryRecordModel

CSV_SALARIES = Path(__file__).parent.parent / "data" / "Latest_Data_Science_Salaries.csv"

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

    # put the salaries into db
    df = pd.read_csv(CSV_SALARIES)
    df = df[df["Job Title"].isin(SELECTED_TITLES)].reset_index(drop=True)


    df = df.rename(columns=lambda c: c.lower().replace(" ", "_"))

    records = []
    for rec in df.to_dict("records"):
        SalaryRecordModel(**rec)       
        records.append(rec)

    salary_coll.delete_many({})       
    if records:
        salary_coll.insert_many(records)

    print(f"Inserted {salary_coll.count_documents({})} salary records into salaries_filtered.")

if __name__ == "__main__":
    main()
