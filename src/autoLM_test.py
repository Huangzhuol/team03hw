import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from flaml import AutoML
import joblib


df = pd.read_csv("./result/filtered_salaries.csv")          
y = df.pop("salary_in_usd")
X = df                                  


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# start to run AutoML (which is call the api)
automl = AutoML()
automl.fit(
    X_train,
    y_train,
    task="regression",
    metric="mae",      
    time_budget=120,     
    log_file_name="flaml.log"
)

y_pred = automl.predict(X_test)

mae   = mean_absolute_error(y_test, y_pred)
rmse  = mean_squared_error(y_test, y_pred) ** 0.5
smape = np.mean(200. * np.abs(y_pred - y_test) /
                (np.abs(y_pred) + np.abs(y_test)))


print(f"\nBest estimator : {automl.model.estimator}")
print(f"MAE   : {mae:.2f}")
print(f"RMSE  : {rmse:.2f}")
print(f"SMAPE : {smape:.2f}%")


joblib.dump(automl, "flaml_salary.pkl")
