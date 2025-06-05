# team03hw:Job Salaries Analyze
## Description
This repository contains the implementation of Job Salaries Analyze, a visual analytics platform designed to forecast future salaries and uncover key influencing factors in the data science job market. Our system combines state-of-the-art time-series forecasting using the Temporal Fusion Transformer (TFT) with interactive visualizations built in React.js and D3.js to deliver an informative and intuitive experience for job seekers and career planners.

Traditional salary platforms focus only on historical averages and lack predictive capabilities. Our system addresses this gap by providing dynamic predictions for salaries in 2025 and 2026, leveraging data from 2020–2024. The platform supports exploration by job title, experience level, location, and more—enabling users to understand trends, compare roles across regions, and identify growth opportunities.

Users begin with an overview bar chart of median salaries by role, then drill into details via a choropleth map (regional comparisons), heatmap (experience vs. region), line chart (salary trends), and pie chart (feature importance from TFT). All views are interlinked, allowing seamless exploration of salary dynamics. In addition to accurate forecasting, we emphasize model interpretability by showing how different input features influence predictions.

This project empowers individuals to make informed career decisions through transparent AI-driven forecasting and engaging visual storytelling.
## Installation
You should get the install and set up the code as following:

### Clone the Repository
```bash
git clone https://github.com/Huangzhuol/team03hw.git
cd team03hw
```
### Install Dependencies
```bash
pip install -r requirements.txt
```
If you still have problem like that "ImportError: cannot import name 'AutoML' from 'flaml'"
```bash
pip install "flaml[automl]"
```
### Dataset
Our project has included the dataset in `data/salaries.csv`


This dataset is not only used for the data import function of the backend's `import.py`,but also for the algorithm part.

The `main.py` use the dataset to generate `attention_summary.csv`,`decoder_variable_importances.csv`,`encoder_variable_importances.csv` and `static_variable_importances.csv` in total 4 weight csv documents. `TFT_Predictions.csv` is also based on it.

The `test.py` use the dataset to generate `TFTtest_Predictions.csv`.


Our dataset is based on: https://www.kaggle.com/datasets/samithsachidanandan/the-global-ai-ml-data-science-salary-for-2025

## Execution
### Model(src foler)
| File Name                | Description                                                               |
|--------------------------|---------------------------------------------------------------------------|
| autoLM_data_preprocess.py | Return filtered_salaries.csv for AutoLM evaluation.                      |
| autoLM_test.py           | Return MAE, RMSE, and SMAPE of prediction 2025 data as AutoLM evaluation. |
| main.py                  | Return the prediction data for 2025–2026 to the front end for display.    |
| test.py                  | Return MAE, RMSE, and SMAPE of prediction 2025 data as TFT evaluation.    |

---
#### Quick Start
```bash
python autoLM_data_preprocess.py
python autoLM_test.py
python main.py
python test.py  
```

reference LINK:https://pytorch-forecasting.readthedocs.io/en/latest/tutorials/stallion.html#Interpret-model
### Backend
#### Quick Start

```bash
# before that you need to intall the requirements.txt
cd server

# import the data first by running this command.
python import_data.py

# Run dev server
uvicorn main:app --reload --port 8000
```

The API will be live at [**http://127.0.0.1:8000**](http://127.0.0.1:8000).

---

#### Endpoint Reference

| Method | Path                 | Description                            |
| ------ | -------------------- | -------------------------------------- |
| GET    | `/records`           | Return *all* records.                  |
| GET    | `/records/{dataset}` | Return records for a specific dataset. |
| GET    | `/salaries`           | Return *all* salaries information.    |
| GET    | `/salaries/{job_title}`| Return salaries for this job_title.    |
| GET    | `/salaries/{job_title}/experience_levels`| Return the type of experience_levels and its number for this job_title.    |
| GET    | `/salaries/{job_title}/{experience_level}`| Return salaries for this job_title and this experience_level.    |
| GET    | `/salary_location`           | Return the type of company_location and its number.   |
| GET    | `/salary_location/{company_location}`           | Return the salaries by company_location.   |
| GET    | `/salary_location/{company_location}/{job_title}`           | Return the salaries by company_location and job_title.   |
| GET    | `/avg_salaries`           | Return job_title and its avg_salaries    |
| GET    | `/avg_salaries/{job_title}`           | Return experience level and its avg_salaries for a specific job_title   |
| GET    | `/tft_predictions`           | Return *all* tft predictions records.                  |
| GET    | `/avg_sal_by_year/{job_title}`           | Return average salaries for each year and each experience_level in job_title.                  |
---

> Replace `{dataset}` with one of the names listed below.

### Available Datasets

Currently shipped datasets:

1. *attention_summary* — key is Encoder Step, value is Attention Weight.

2. *decoder_variable_importances* - key is Variable, value is Importance (%)

3. *encoder_variable_importances* - key is Variable, value is Importance (%)

4. *static_variable_importances* - key is Variable, value is Importance (%)

---
> Replace `{job_title}` with one of the names listed below.

### Available job_title
1. Data Analyst

2. Data Analytics Manager

3. Data Architect

4. Data Engineer

5. Data Scientist

6. Head of Data

7. Machine Learning Engineer

8. Machine Learning Scientist

9. Research Scientist

---

> Replace `{experience_level}` with one of the names listed below.
##### Tips: not every job_title has all of the experience_level below. Check with api GET "/salaries/{job_title}/experience_levels" first before you call it.

### Available experience_level
1. Entry

2. Mid

3. Senior

4. Executive

### Frontend
#### Quick Start
```bash
cd client

# Install required Node.js packages
npm install

# Start the React development server
npm run dev
```
Visit the frontend in your browser :  [**http://localhost:5173**](http://localhost:5173).

