import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import json

# Load dataset
df = pd.read_csv(
    r"E:\CAPSTRONE PROJECT\Ml__Service\healthcare_capacity_data.csv"
)

# Convert date
df["date"] = pd.to_datetime(df["date"])

# Sort data
df = df.sort_values(["department", "date"])

# Store results
evaluation_results = []
all_forecasts = []

# Forecast department by department
for department in df["department"].unique():

    dept_data = df[df["department"] == department].copy()

    # Create day number
    dept_data["day_number"] = range(1, len(dept_data) + 1)

    # -------------------------
    # MODEL EVALUATION
    # -------------------------

    train_data = dept_data.iloc[:-14]
    test_data = dept_data.iloc[-14:]

    model = LinearRegression()

    model.fit(
        train_data[["day_number"]],
        train_data["patient_demand"]
    )

    test_predictions = model.predict(
        test_data[["day_number"]]
    )

    # ML Model MAE
    mae = mean_absolute_error(
        test_data["patient_demand"],
        test_predictions
    )

    # -------------------------
    # BASELINE
    # -------------------------

    baseline_predictions = dept_data["patient_demand"].shift(1)
    baseline_predictions = baseline_predictions.loc[test_data.index]

    baseline_mae = mean_absolute_error(
        test_data["patient_demand"],
        baseline_predictions
    )

    evaluation_results.append({
        "Department": department,
        "Linear Regression MAE": round(mae, 2),
        "Baseline MAE": round(baseline_mae, 2)
    })

    # -------------------------
    # FINAL MODEL
    # -------------------------

    final_model = LinearRegression()

    final_model.fit(
        dept_data[["day_number"]],
        dept_data["patient_demand"]
    )

    # Next 7 days
    future_days = pd.DataFrame(
        [[len(dept_data) + i] for i in range(1, 8)],
        columns=["day_number"]
    )

    future_predictions = final_model.predict(future_days)

    available_capacity = dept_data["available_capacity"].iloc[-1]

    # -------------------------
    # 7-DAY FORECAST
    # -------------------------

    for i, prediction in enumerate(
        future_predictions,
        start=1
    ):

        capacity_gap = prediction - available_capacity

        if capacity_gap > 0:
            status = "Shortage Expected"
        else:
            status = "Capacity Sufficient"

        all_forecasts.append({
            "Department": department,
            "Day": i,
            "Predicted Demand": round(float(prediction), 2),
            "Available Capacity": int(available_capacity),
            "Capacity Gap": round(float(capacity_gap), 2),
            "Status": status
        })

# Final output
result = {
    "dataset_records": len(df),
    "evaluation": evaluation_results,
    "forecast": all_forecasts
}

# Output structured JSON
print(json.dumps(result, indent=2))