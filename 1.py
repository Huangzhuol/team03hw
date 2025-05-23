import pandas as pd
from pytorch_forecasting.data import TimeSeriesDataSet, GroupNormalizer
from pytorch_forecasting.models import TemporalFusionTransformer
from pytorch_forecasting.metrics import SMAPE
from lightning.pytorch import Trainer

def import_data():
    # Load dataset
    df = pd.read_csv("data/Latest_Data_Science_Salaries.csv")
    df = df.dropna(subset=["Salary in USD"])
    length_df=len(df)
    unique_job_titles = df["Job Title"].dropna().unique()
    print(f"Unique job titles: {unique_job_titles}")
    job_title_counts = df["Job Title"].value_counts()
    # small_counts = job_title_counts[job_title_counts < 5]

    # print(small_counts)
    all_predictions = []

    for job_title in unique_job_titles:
        print(f"\nProcessing job title: {job_title}")
        job_df = df[df["Job Title"] == job_title].copy()
        job_df["job_id"] = job_title
        job_df["time_idx"] = job_df["Year"] - job_df["Year"].min()
        job_df = job_df.sort_values(["job_id", "time_idx"]).reset_index(drop=True)

        if len(job_df) < 5:
            print(f"Skipping {job_title} due to insufficient data")
            continue

        last_time_idx = job_df["time_idx"].max()
        future_years = [2025, 2026]
        future_df = pd.DataFrame({
            "Year": future_years,
            "time_idx": [last_time_idx + i + 1 for i in range(len(future_years))],
            "job_id": [job_title] * len(future_years),
            "Company Size": ["Medium"] * len(future_years),
            "Salary in USD": [0.0] * len(future_years)
        })

        model_input_df = pd.concat([job_df, future_df], ignore_index=True)
        model_input_df = model_input_df.sort_values(["job_id", "time_idx"])

        max_encoder_length = 5
        max_prediction_length = 2

        try:
            training_data = TimeSeriesDataSet(
                model_input_df,
                time_idx="time_idx",
                target="Salary in USD",
                group_ids=["job_id"],
                max_encoder_length=max_encoder_length,
                max_prediction_length=max_prediction_length,
                static_categoricals=["job_id", "Company Size"],
                time_varying_known_reals=["time_idx", "Year"],
                time_varying_unknown_reals=["Salary in USD"],
                allow_missing_timesteps=True,
                target_normalizer=GroupNormalizer(groups=["job_id"]), 
            )
        except Exception as e:
            print(f"Failed to create TimeSeriesDataSet for {job_title}: {e}")
            continue

        train_dataloader = training_data.to_dataloader(train=True, batch_size=32, num_workers=0)

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

        trainer = Trainer(max_epochs=1, gradient_clip_val=0.1, enable_model_summary=False)
        trainer.fit(tft, train_dataloaders=train_dataloader)

        full_data = TimeSeriesDataSet(
            model_input_df,
            time_idx="time_idx",
            target="Salary in USD",
            group_ids=["job_id"],
            max_encoder_length=max_encoder_length,
            max_prediction_length=max_prediction_length,
            static_categoricals=["job_id", "Company Size"],
            time_varying_known_reals=["time_idx", "Year"],
            time_varying_unknown_reals=["Salary in USD"],
            allow_missing_timesteps=True,
            target_normalizer=GroupNormalizer(groups=["job_id"]),
        )

        full_dataloader = full_data.to_dataloader(train=False, batch_size=32, num_workers=0)
        predictions, x = tft.predict(full_dataloader, mode="prediction", return_x=True)[:2]
        preds = predictions[0].detach().numpy().flatten()
        time_idx = x["decoder_time_idx"][0].detach().numpy().flatten()

        min_year = min(future_years)
        years = time_idx + min_year
        future_mask = years >= 2025

        df_pred = pd.DataFrame({
            "Job Title": job_title,
            # "time_idx": time_idx[future_mask],
            "Predicted Salary USD": preds[future_mask],
            "Year": future_years
        })

        all_predictions.append(df_pred)

    # Save all predictions to a single CSV
    result_df = pd.concat(all_predictions, ignore_index=True)
    result_df.to_csv("TFT_Future_Predictions_All_Jobs.csv", index=False)
    print("\nAll job title predictions saved.")

def main():
    import_data()


if __name__ == "__main__":
    main()
