import pandas as pd
import matplotlib.pyplot as plt
from pytorch_forecasting.data import TimeSeriesDataSet, GroupNormalizer
from pytorch_forecasting.models import TemporalFusionTransformer
from pytorch_forecasting.metrics import SMAPE
from lightning.pytorch import Trainer
from sklearn.metrics import mean_absolute_error, mean_squared_error
import torch
import numpy as np
import math
import os

def test():
    # Create result folder
    os.makedirs("result", exist_ok=True)

    # Load and preprocess dataset
    df = pd.read_csv("./data/salaries.csv")
    df.drop(columns=["salary_currency", "salary"], inplace=True, errors="ignore")
    df = df.dropna(subset=["salary_in_usd"])
    df.rename(columns={
        "salary_in_usd": "Salary in USD",
        "job_title": "Job Title",
        "experience_level": "Experience Level",
        "work_year": "Year"
    }, inplace=True)

    # Filter to top 50 job titles
    top_jobs = df["Job Title"].value_counts().nlargest(50).index.tolist()
    df = df[df["Job Title"].isin(top_jobs)]

    # Assign series_id and time_idx
    df["series_id"] = df.groupby(["Job Title", "Experience Level"]).ngroup()
    df["time_idx"] = df["Year"] - df["Year"].min()
    df = df.sort_values(["series_id", "time_idx"]).reset_index(drop=True)

    # Config
    max_encoder_length = 3
    max_prediction_length = 1
    target_year = 2025

    # Split into train and predict sets
    train_df = df[df["Year"] <= 2024].copy()
    categorical_columns = train_df.select_dtypes(include='object').columns.tolist()
    predict_df = df[df["Year"] == target_year].copy()

    # Filter valid series (length ≥ encoder + decoder)
    min_required = max_encoder_length + max_prediction_length

    def is_valid_group(df_group):
        return df_group["time_idx"].nunique() >= min_required and df_group["time_idx"].max() >= (
            df_group["time_idx"].min() + max_encoder_length
        )

    # Filter train_df to only valid series
    valid_train_df = train_df.groupby("series_id").filter(is_valid_group)

    # Proceed only if not empty
    if valid_train_df.empty:
        raise ValueError("No valid training data found after filtering. Consider lowering encoder/prediction length.")

    # Restrict all dfs to valid series_id
    valid_series_ids = valid_train_df["series_id"].unique()
    train_df = train_df[train_df["series_id"].isin(valid_series_ids)]
    predict_df = predict_df[predict_df["series_id"].isin(valid_series_ids)]

    for cat_col in categorical_columns:
        valid_categories = train_df[cat_col].unique()
        predict_df = predict_df[predict_df[cat_col].isin(valid_categories)]

    model_input_df = pd.concat([train_df, predict_df], ignore_index=True)


    # Ensure categorical type consistency
    for col in model_input_df.select_dtypes(include='object').columns:
        model_input_df[col] = model_input_df[col].astype(str)

    # Feature setup
    target_col = "Salary in USD"
    time_col = "time_idx"
    known_reals = ["Year", time_col]
    unknown_reals = [target_col]
    static_categoricals = []
    time_varying_categoricals = []
    static_reals = ["remote_ratio"]

    for col in model_input_df.columns:
        if col in [target_col, time_col, "series_id"]:
            continue
        elif model_input_df[col].dtype == "object":
            if model_input_df[col].nunique() < 100:
                if col in ["Job Title", "Experience Level"]:
                    time_varying_categoricals.append(col)
                else:
                    static_categoricals.append(col)
        else:
            if col not in known_reals + unknown_reals + static_reals:
                known_reals.append(col)

    # Build datasets
    training_data = TimeSeriesDataSet(
        train_df,
        time_idx=time_col,
        target=target_col,
        group_ids=["series_id"],
        max_encoder_length=max_encoder_length,
        max_prediction_length=max_prediction_length,
        static_reals=static_reals,
        static_categoricals=static_categoricals,
        time_varying_known_reals=known_reals,
        time_varying_unknown_reals=unknown_reals,
        time_varying_known_categoricals=time_varying_categoricals,
        allow_missing_timesteps=True,
        target_normalizer=GroupNormalizer(groups=["series_id"]),
    )

    train_dataloader = training_data.to_dataloader(train=True, batch_size=32, num_workers=4, persistent_workers=True)
    full_data = TimeSeriesDataSet.from_dataset(training_data, model_input_df, predict=True, stop_randomization=True)
    full_dataloader = full_data.to_dataloader(train=False, batch_size=32, num_workers=4, persistent_workers=True)

    # Train model
    tft = TemporalFusionTransformer.from_dataset(
        training_data,
        learning_rate=0.03,
        hidden_size=8,
        attention_head_size=1,
        dropout=0.1,
        loss=SMAPE(),
        log_interval=10,
        reduce_on_plateau_patience=2,
    )
    tft.save_hyperparameters(ignore=["loss", "logging_metrics"])
    trainer = Trainer(max_epochs=3, gradient_clip_val=0.1, enable_model_summary=False, log_every_n_steps=1)
    trainer.fit(tft, train_dataloaders=train_dataloader)
    
    # raw_predictions= tft.predict(full_dataloader, mode="raw", return_x=True)
    # raw_output = dict(raw_predictions.output._asdict())
    # max_len = tft.hparams.max_encoder_length
    # # clamped the encoder_lengths
    # if raw_output["encoder_lengths"].max() >= max_len:
    #     print(f"[Fix] Clipping encoder_lengths > {max_len - 1}")
    #     raw_output["encoder_lengths"] = torch.clamp(
    #         raw_output["encoder_lengths"], max=max_len - 1
    #     )
    # interpretation = tft.interpret_output(raw_output, reduction="sum")

    # tft.plot_interpretation(interpretation)
    # plt.show()
    # Predict 2025
    result = tft.predict(full_dataloader, mode="prediction", return_x=True)
    predictions = result[0]
    x=result[1]
    all_preds = np.concatenate([pred.detach().cpu().numpy().flatten() for pred in predictions])

    original_series_ids = train_df["series_id"].unique()
    original_series_ids.sort()  
    series_ids_tensor = x["groups"].squeeze(-1)
    predicted_series_ids = series_ids_tensor.detach().cpu().numpy()
    mapped_series_ids =  original_series_ids[predicted_series_ids]

    predictable_index = pd.DataFrame({
        "series_id": mapped_series_ids,
        "time_idx": 5
    })

    # Add predictions
    predictable_index["Predicted Salary USD"] = all_preds
    # Merge with future_df
    future_df_filtered = predict_df.merge(
        predictable_index,
        on=["series_id", "time_idx"],
        how="inner"
    )
    df_pred = future_df_filtered[["Job Title", "Experience Level", "Year", "Salary in USD","Predicted Salary USD"]]
    df_pred.to_csv("result/TFTtest_Predictions.csv", index=False)

    # # Evaluation metrics
    true_vals =  df_pred["Salary in USD"].values
    pred_vals = df_pred["Predicted Salary USD"].values
    # # Print results only
    mae = mean_absolute_error(true_vals, pred_vals)
    mse = mean_squared_error(true_vals, pred_vals)
    rmse = math.sqrt(mse)

    # SMAPE calculation (as %)
    smape = 100 * np.mean(
        2 * np.abs(pred_vals - true_vals) / (np.abs(true_vals) + np.abs(pred_vals) + 1e-8)
    )

    print(f"Evaluated on {len(df_pred)} rows")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"SMAPE: {smape:.2f}%")
    
if __name__ == "__main__":
    test()
