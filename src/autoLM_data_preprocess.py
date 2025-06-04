import pandas as pd

test_df = pd.read_csv("./result/TFTtest_Predictions.csv")
salaries_df = pd.read_csv("./data/salaries.csv")

job_level_combos = test_df[["job_title", "experience_level"]].drop_duplicates()

merged_df = salaries_df.merge(job_level_combos, on=["job_title", "experience_level"])

merged_df.to_csv("result/filtered_salaries.csv", index=False)

print("filtered_salaries.csv saved")
