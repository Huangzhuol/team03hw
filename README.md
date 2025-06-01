# team03hw

now it just realize with the factor "company size"= Medium, and it want to realize that it has  a front end, so user can select all known columns or some columns to predict future salary,



The model has inbuilt interpretation capabilities due to how its architecture is build. Let’s see how that looks. We first calculate interpretations with interpret_output() and plot them subsequently with plot_interpretation().


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

> Replace `{dataset}` with one of the names listed below.

---

## Available Datasets

Currently shipped datasets:

1. *attention_summary* — key is Encoder Step, value is Attention Weight.

2. *decoder_variable_importances* - key is Variable, value is Importance (%)

3. *encoder_variable_importances* - key is Variable, value is Importance (%)

4. *static_variable_importances* - key is Variable, value is Importance (%)


