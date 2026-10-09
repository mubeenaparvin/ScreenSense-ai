import pandas as pd
import numpy as np

# Make results reproducible
np.random.seed(42)

# Number of records
n = 1000

# Generate sample data
data = {
    "age": np.random.randint(15, 51, n),
    "daily_screen_time": np.round(np.random.uniform(2, 12, n), 1),
    "social_media_time": np.round(np.random.uniform(0, 6, n), 1),
    "gaming_time": np.round(np.random.uniform(0, 5, n), 1),
    "study_work_time": np.round(np.random.uniform(1, 8, n), 1),
    "phone_unlocks": np.random.randint(10, 151, n),
    "night_screen_time": np.round(np.random.uniform(0, 4, n), 1),
    "sleep_duration": np.round(np.random.uniform(4, 9, n), 1),
    "physical_activity": np.random.randint(0, 121, n),
    "breaks_per_day": np.random.randint(0, 11, n),
    "weekend_screen_time": np.round(np.random.uniform(3, 15, n), 1)
}

df = pd.DataFrame(data)

# Calculate risk score
def calculate_risk(row):
    score = 0

    if row["daily_screen_time"] > 8:
        score += 2

    if row["social_media_time"] > 3:
        score += 1

    if row["gaming_time"] > 2:
        score += 1

    if row["phone_unlocks"] > 80:
        score += 1

    if row["night_screen_time"] > 2:
        score += 2

    if row["sleep_duration"] < 6:
        score += 2

    if row["physical_activity"] < 30:
        score += 1

    if row["breaks_per_day"] < 3:
        score += 1

    if row["weekend_screen_time"] > 10:
        score += 1

    # Convert score into risk category
    if score <= 3:
        return "Low"
    elif score <= 7:
        return "Moderate"
    else:
        return "High"


# Create risk level
df["risk_level"] = df.apply(calculate_risk, axis=1)

# Save dataset
df.to_csv("dataset/screen_time_data.csv", index=False)

print("Dataset created successfully!")
print("Number of records:", len(df))
print("\nFirst 5 records:")
print(df.head())

print("\nRisk distribution:")