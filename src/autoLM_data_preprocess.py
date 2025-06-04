import pandas as pd

# read the csv
test_df = pd.read_csv("./result/TFTtest_Predictions.csv")
salaries_df = pd.read_csv("./data/salaries.csv")

# the name is different. we
test_df = test_df.rename(columns={
    "Job Title": "job_title",
    "Experience Level": "experience_level"
})

job_level_combos = test_df[["job_title", "experience_level"]].drop_duplicates()

merged_df = salaries_df.merge(job_level_combos, on=["job_title", "experience_level"])

merged_df.to_csv("result/filtered_salaries.csv", index=False)

print("filtered_salaries.csv saved")
