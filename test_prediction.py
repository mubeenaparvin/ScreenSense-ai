import joblib
import pandas as pd

# Load the trained model
model = joblib.load("model/screen_time_model.pkl")

# Sample person's screen-time details
data = {
    "age": [22],
    "daily_screen_time": [9.5],
    "social_media_time": [4],
    "gaming_time": [2.5],
    "study_work_time": [3],
    "phone_unlocks": [100],
    "night_screen_time": [2.5],
    "sleep_duration": [5.5],
    "physical_activity": [20],
    "breaks_per_day": [2],
    "weekend_screen_time": [12]
}

# Convert data into DataFrame
input_data = pd.DataFrame(data)

# Make prediction
prediction = model.predict(input_data)

# Display result
print("Predicted Risk Level:", prediction[0])