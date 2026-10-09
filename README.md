# ScreenSense AI

A web-based screen-time risk prediction app built with Flask and machine learning. It predicts whether a user's screen-time habits are **Low**, **Moderate**, or **High** risk.

## Features
- User module: register/login, dashboard, prediction by manual entry or CSV upload, history, analytics, reports, settings
- Admin module: dashboard, user and prediction management, reports, PDF download

## How it works
A Random Forest classifier is trained on five inputs: daily screen time, social media time, gaming time, night-time usage, and weekend usage. The trained model (`model/screen_time_model.pkl`) is loaded by the Flask app to give real-time predictions. Test accuracy is about 71%.

## Tech Stack
Python, Flask, Pandas, Scikit-learn, Joblib, SQLite, HTML, CSS

## How to Run
1. Install the libraries: `pip install -r requirements.txt`
2. Create the database: `python database.py`
3. Create the admin account: `python create_admin.py`
4. Start the app: `python app.py`
5. Open `http://127.0.0.1:5000` in your browser

To retrain the model: run `python create_dataset.py`, then `python train_model.py`.

## Demo Admin Login
Email: admin@screensense.com | Password: admin123 (demo only)

## Author
Mubeena Parvin V.N
