import pandas as pd
import matplotlib.pyplot as plt
from pytorch_forecasting.data import TimeSeriesDataSet, GroupNormalizer
from pytorch_forecasting.models import TemporalFusionTransformer
from pytorch_forecasting.metrics import SMAPE
from lightning.pytorch import Trainer
import torch
import numpy as np
import os

def main():
    # Load and preprocess dataset
    os.makedirs("result", exist_ok=True)
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

    # Assign series_id based on job + experience
    df["series_id"] = df.groupby(["Job Title", "Experience Level"]).ngroup()
    df["time_idx"] = df["Year"] - df["Year"].min()

    # Sort for consistency
    df = df.sort_values(["series_id", "time_idx"]).reset_index(drop=True)

    # Generate 2 future rows per unique (Job Title, Experience Level)
    unique_combos = df[["Job Title", "Experience Level"]].drop_duplicates()
    future_years = [2025, 2026]
    last_time_idx = df["time_idx"].max()

    future_rows = []
    for _, row in unique_combos.iterrows():
        job = str(row["Job Title"])
        exp = str(row["Experience Level"])
        for i, year in enumerate(future_years):
            future_rows.append({
                "Job Title": job,
                "Experience Level": exp,
                "Year": year,
                "time_idx": last_time_idx + i + 1,
                "Salary in USD": 0.0
            })

    # Create future DataFrame
    future_df = pd.DataFrame(future_rows)
    
    # Reassign series_id
    future_df["series_id"] = future_df.groupby(["Job Title", "Experience Level"]).ngroup()

    for col in df.columns:
        if col not in future_df.columns:
            # Attempt to fill from a representative value or default
            if df[col].dtype == "object":
                default_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
                future_df[col] = default_val
            else:
                default_val = df[col].median() if not df[col].isna().all() else 0.0
                future_df[col] = default_val

    df["series_id"] = df.groupby(["Job Title", "Experience Level"]).ngroup()

    # Combine
    model_input_df = pd.concat([df, future_df], ignore_index=True)
    model_input_df = model_input_df.sort_values(["series_id", "time_idx"]).reset_index(drop=True)
    # Ensure string type consistency for encoding
    for col in model_input_df.select_dtypes(include='object').columns:
        model_input_df[col] = model_input_df[col].astype(str)

    # print(model_input_df)
    # Identify model input features
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
            if col not in known_reals + unknown_reals+static_reals:
                known_reals.append(col)

    max_encoder_length = 5
    max_prediction_length = 2

    # Build datasets
    training_data = TimeSeriesDataSet(
        model_input_df,
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

    train_dataloader = training_data.to_dataloader(train=True, batch_size=32, num_workers=4,persistent_workers=True)
    full_data = TimeSeriesDataSet.from_dataset(training_data,model_input_df,predict=True,stop_randomization=True)
    full_dataloader = full_data.to_dataloader(train=False, batch_size=32, num_workers=4,persistent_workers=True)
    
    # Model definition and training
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

    trainer = Trainer(max_epochs=10, gradient_clip_val=0.1, enable_model_summary=False,log_every_n_steps=1)
    trainer.fit(tft, train_dataloaders=train_dataloader)
    
    # Get weight csv
    raw_predictions= tft.predict(full_dataloader, mode="raw", return_x=True)
    raw_output = dict(raw_predictions.output._asdict())
    max_len = tft.hparams.max_encoder_length
    # clamped the encoder_lengths
    if raw_output["encoder_lengths"].max() >= max_len:
        print(f"[Fix] Clipping encoder_lengths > {max_len - 1}")
        raw_output["encoder_lengths"] = torch.clamp(
            raw_output["encoder_lengths"], max=max_len - 1
        )
    interpretation = tft.interpret_output(raw_output, reduction="sum")

    # Get static variable importances
    static_importance_values = interpretation["static_variables"].detach().cpu().numpy()
    static_variable_names = training_data.static_categoricals+\
                            training_data.static_reals
    static_df = pd.DataFrame({
        "Variable": static_variable_names,
        "Importance (%)": static_importance_values
    })
    static_df = static_df.sort_values(by="Importance (%)", ascending=False)
    static_df.to_csv("result/static_variable_importances.csv", index=False)
    print("Saved static variable importances to 'static_variable_importances.csv'")

    # Extract encoder variable importances
    encoder_importance_values = interpretation["encoder_variables"].detach().cpu().numpy()
    encoder_variable_names = training_data.time_varying_known_reals + \
                            training_data.time_varying_unknown_reals + \
                            training_data.time_varying_known_categoricals

    encoder_df = pd.DataFrame({
        "Variable": encoder_variable_names,
        "Importance (%)": encoder_importance_values
    }).sort_values(by="Importance (%)", ascending=False)
    encoder_df.to_csv("result/encoder_variable_importances.csv", index=False)
    print("Saved encoder variable importances to 'encoder_variable_importances.csv'")

    # Extract decoder variable importances
    decoder_importance_values = interpretation["decoder_variables"].detach().cpu().numpy()
    decoder_variable_names = training_data.time_varying_known_reals + \
                            training_data.time_varying_known_categoricals

    decoder_df = pd.DataFrame({
        "Variable": decoder_variable_names,
        "Importance (%)": decoder_importance_values
    }).sort_values(by="Importance (%)", ascending=False)
    decoder_df.to_csv("result/decoder_variable_importances.csv", index=False)
    print("Saved decoder variable importances to 'decoder_variable_importances.csv'")

    if "attention" in interpretation:
        attention = interpretation["attention"]
        attention_np = attention.detach().cpu().numpy()  # shape: (encoder_length,)

        encoder_steps = list(range(len(attention_np)))
        attention_df = pd.DataFrame({
            "Encoder Step": encoder_steps,
            "Attention Weight": attention_np
        })

        attention_df.to_csv("result/attention_summary.csv", index=False)
        print("Saved summary attention weights to 'result/attention_summary.csv'")
    else:
        print("No attention data found in interpretation.")

    # tft.plot_interpretation(interpretation)
    # plt.show()

    # do prediction
    result = tft.predict(full_dataloader, mode="prediction", return_x=True)
    predictions = result[0]
    x = result[1]

    all_preds = np.concatenate([pred.detach().cpu().numpy().flatten() for pred in predictions])

    n_series = len(set(full_data.index["sequence_id"].tolist()))

    # Repeat each series_id twice (for 2 time steps: 6, 7)
    series_ids = np.repeat(list(set(full_data.index["sequence_id"])), 2)
    time_idxs = [6, 7] * n_series  # [6, 7, 6, 7, ..., 6, 7] for each series

    predictable_index = pd.DataFrame({
        "series_id": series_ids,
        "time_idx": time_idxs
    })

    # Add predictions
    predictable_index["Predicted Salary USD"] = all_preds
    # Merge with future_df
    future_df_filtered = future_df.merge(
        predictable_index,
        on=["series_id", "time_idx"],
        how="inner"
    )
    df_pred = future_df_filtered[["Job Title", "Experience Level", "Year", "Predicted Salary USD"]]
    df_pred.to_csv("result/TFT_Predictions.csv", index=False)
    print(df_pred.head())


if __name__ == "__main__":
    main()
