import pandas as pd
from pytorch_forecasting.data import TimeSeriesDataSet, GroupNormalizer
from pytorch_forecasting.models import TemporalFusionTransformer
from pytorch_forecasting.metrics import SMAPE
from lightning.pytorch import Trainer


def import_data():
    # Load dataset
    df = pd.read_csv("./data/Latest_Data_Science_Salaries.csv")
    df = df.dropna(subset=["Salary in USD"])

    unique_job_titles = df["Job Title"].dropna().unique()
    count_unique = len(unique_job_titles)

    # Prepare columns
    df = df[df["Job Title"] == "Data Scientist"]
    df["job_id"] = "Data Scientist"
    df["time_idx"] = df["Year"] - df["Year"].min()
    df = df.sort_values(["job_id", "time_idx"])
    df = df.reset_index(drop=True)
    length_df=len(df)
    last_time_idx = df["time_idx"].max()
    # Future years for forecasting
    future_years = [2025, 2026]
    future_df = pd.DataFrame({
        "Year": future_years,
        "time_idx": [last_time_idx + i + 1 for i in range(len(future_years))],
        "job_id": ["Data Scientist"] * len(future_years),
        "Company Size": ["Medium"] * len(future_years)
    })

    # Combine historical and future
    future_df["Salary in USD"] = 0.0  
    model_input_df = pd.concat([df, future_df], ignore_index=True)
    model_input_df = model_input_df.sort_values(["job_id", "time_idx"])


    max_encoder_length = 5
    max_prediction_length = 2

    # Training dataset (only historical data)
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

    train_dataloader = training_data.to_dataloader(train=True, batch_size=32, num_workers=0)

    # Initialize model
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

    # Train model
    # adjust parameter
    trainer = Trainer(max_epochs=1, gradient_clip_val=0.1, enable_model_summary=False)
    trainer.fit(tft, train_dataloaders=train_dataloader)

    # Full dataset including future for prediction
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

    # Predict on the full dataset (train=False)
    full_dataloader = full_data.to_dataloader(train=False, batch_size=32, num_workers=0)
    predictions, x= tft.predict(full_dataloader, mode="prediction", return_x=True)[:2]

    preds = predictions[0].detach().numpy().flatten()

    # Corresponding the index of the model_input_df
    time_idx = x["decoder_time_idx"][0].detach().numpy().flatten()

    # min year means 2025
    min_year = min(future_years)    
    years = time_idx + min_year

    # Only future predictions
    future_mask = years >= 2025
    df_pred = pd.DataFrame({
        # "time_idx": time_idx[future_mask],
        "Predicted Salary USD": preds[future_mask],
        "Year": years[future_mask]-length_df
    })

    # Save result
    df_pred.to_csv("TFT_Future_Prediction_2025_2026.csv", index=False)
    print(df_pred)


def main():
    import_data()


if __name__ == "__main__":
    main()
