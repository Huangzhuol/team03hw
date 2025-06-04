# team03hw:Job Salaries Analyze




## Model(src foler)
| file name |  Description                            |
| ------ | - -------------------------------------- |
|autoLM_data_preprocess.py  | Return filtered_salaries.csv for AutoLM evaluation.             |
|autoLM_test.py | Return MAE,RMSE,and SMAPE of prediction 2025 data as AutoLM evaluation. |
|main.py    | Return the prediction data for 2025-2026 to the front end for display.   |
|test.py   |Return MAE,RMSE,and SMAPE of prediction 2025 data as TFT evaluation.   |

### Quick Start
```bash
python autoLM_data_preprocess.py/autoLM_test.py/main.py/test.py  
```

reference LINK:https://pytorch-forecasting.readthedocs.io/en/latest/tutorials/stallion.html#Interpret-model
## Backend
### Quick Start

```bash
# before that you need to intall the requirements.txt
cd server

# Run dev server
uvicorn main:app --reload --port 8000
```

The API will be live at [**http://127.0.0.1:8000**](http://127.0.0.1:8000).

---

### Endpoint Reference

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

## Available Datasets

Currently shipped datasets:

1. *attention_summary* — key is Encoder Step, value is Attention Weight.

2. *decoder_variable_importances* - key is Variable, value is Importance (%)

3. *encoder_variable_importances* - key is Variable, value is Importance (%)

4. *static_variable_importances* - key is Variable, value is Importance (%)

---
> Replace `{job_title}` with one of the names listed below.

## Available job_title
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
#### Tips: not every job_title has all of the experience_level below. Check with api GET "/salaries/{job_title}/experience_levels" first before you call it.

## Available experience_level
1. Entry

2. Mid

3. Senior

4. Executive

## Frontend
### Quick Start
```bash
cd client

# Install required Node.js packages
npm install

# Start the React development server
npm run dev
```
Visit the frontend in your browser :  [**http://localhost:5173**](http://localhost:5173).

