import pandas as pd
import numpy as np

# For reproducible results
np.random.seed(42)

# Generate 6 months of dates
dates = pd.date_range(
    start="2026-04-01",
    end="2026-09-30",
    freq="D"
)

# Hospital departments
departments = [
    "Cardiology",
    "General Medicine",
    "Orthopedics",
    "Pediatrics",
    "Dermatology"
]

data = []

# Generate synthetic healthcare operations data
for date in dates:
    for department in departments:

        # Different normal demand for each department
        base_demand = {
            "Cardiology": 45,
            "General Medicine": 65,
            "Orthopedics": 40,
            "Pediatrics": 50,
            "Dermatology": 35
        }[department]

        # Weekend effect
        weekend_effect = -8 if date.dayofweek >= 5 else 0

        # Small monthly trend
        trend = (date - dates[0]).days * 0.03

        # Random variation
        variation = np.random.normal(0, 5)

        # Patient demand
        patient_demand = max(
            10,
            round(base_demand + weekend_effect + trend + variation)
        )

        # Available capacity
        available_capacity = {
            "Cardiology": 50,
            "General Medicine": 70,
            "Orthopedics": 45,
            "Pediatrics": 55,
            "Dermatology": 40
        }[department]

        # Appointment and walk-in counts
        appointments = round(patient_demand * 0.6)
        walk_ins = patient_demand - appointments

        # Referral count
        referrals = max(
            0,
            round(patient_demand * 0.08 + np.random.normal(0, 2))
        )

        # Average waiting time
        average_wait_time = max(
            5,
            round((patient_demand / available_capacity) * 20
                  + np.random.normal(0, 3), 2)
        )

        data.append([
            date.strftime("%Y-%m-%d"),
            department,
            patient_demand,
            available_capacity,
            appointments,
            walk_ins,
            referrals,
            average_wait_time
        ])

# Create DataFrame
df = pd.DataFrame(data, columns=[
    "date",
    "department",
    "patient_demand",
    "available_capacity",
    "appointments",
    "walk_ins",
    "referrals",
    "average_wait_time"
])

# Save dataset
df.to_csv("healthcare_capacity_data.csv", index=False)

print("Dataset created successfully!")
print("Total records:", len(df))

print("\nFirst 10 records:")
print(df.head(10))

print("\nDepartments:")
print(df["department"].unique())