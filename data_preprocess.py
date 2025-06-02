import pandas as pd

test_df = pd.read_csv("TFTtest_Predictions.csv")
salaries_df = pd.read_csv("salaries.csv")

# 提取 test.csv 中唯一的 (Job Title, Experience Level) 组合
job_level_combos = test_df[["job_title", "experience_level"]].drop_duplicates()

# 在 salaries.csv 中筛选出匹配的组合
merged_df = salaries_df.merge(job_level_combos, on=["job_title", "experience_level"])

# 保存到新的 CSV 文件
merged_df.to_csv("filtered_salaries.csv", index=False)

print("filtered_salaries.csv saved")
