
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import joblib
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "screensense_secret_key"

DATABASE = "database/screensense.db"

model = joblib.load("model/screen_time_model.pkl")


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =====================================================
# REGISTER
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        existing_user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:

            message = "Email already registered."

            connection.close()

            return render_template(
                "register.html",
                message=message
            )

        hashed_password = generate_password_hash(password)

        connection.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, hashed_password)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("login"))

    return render_template(
        "register.html",
        message=message
    )


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        account_type = request.form["account_type"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        # ---------------- ADMIN LOGIN ----------------

        if account_type == "admin":

            admin = connection.execute(
                "SELECT * FROM admins WHERE email = ?",
                (email,)
            ).fetchone()

            connection.close()

            if admin and check_password_hash(
                admin["password"],
                password
            ):

                session.clear()

                session["admin_id"] = admin["id"]
                session["admin_name"] = admin["name"]

                return redirect(
                    url_for("admin_dashboard")
                )

            else:

                message = "Invalid admin email or password."

        # ---------------- USER LOGIN ----------------

        else:

            user = connection.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            connection.close()

            if user and check_password_hash(
                user["password"],
                password
            ):

                session.clear()

                session["user_id"] = user["id"]
                session["user_name"] = user["name"]

                return redirect(
                    url_for("dashboard")
                )

            else:

                message = "Invalid user email or password."

    return render_template(
        "login.html",
        message=message
    )


# =====================================================
# USER LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =====================================================
# ADMIN LOGOUT
# =====================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("login"))


# =====================================================
#                    USER SECTION
# =====================================================


# =====================================================
# USER DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    latest_prediction = connection.execute(
        """
        SELECT *
        FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    total_predictions = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()["count"]

    prediction_history = connection.execute(
        """
        SELECT daily_screen_time, prediction_date
        FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date ASC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    screen_time = "--"
    risk_level = "Not Available"

    if latest_prediction:

        screen_time = latest_prediction[
            "daily_screen_time"
        ]

        risk_level = latest_prediction[
            "risk_level"
        ]

    dates = []
    screen_times = []

    for row in prediction_history:

        dates.append(row["prediction_date"])

        screen_times.append(
            row["daily_screen_time"]
        )

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        screen_time=screen_time,
        risk_level=risk_level,
        total_predictions=total_predictions,
        dates=dates,
        screen_times=screen_times
    )


# =====================================================
# USER HISTORY
# =====================================================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    prediction_history = connection.execute(
        """
        SELECT
            daily_screen_time,
            social_media_time,
            gaming_time,
            night_screen_time,
            weekend_screen_time,
            risk_level,
            prediction_date
        FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "history.html",
        history=prediction_history,
        name=session["user_name"]
    )


# =====================================================
# USER ANALYTICS
# =====================================================

@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user_id = session["user_id"]


    # ================= TOTAL PREDICTIONS =================

    total_predictions = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["count"]


    # ================= SCREEN-TIME STATISTICS =================

    statistics = connection.execute(
        """
        SELECT
            AVG(daily_screen_time) AS avg_screen_time,
            MAX(daily_screen_time) AS max_screen_time,
            MIN(daily_screen_time) AS min_screen_time
        FROM predictions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()


    # ================= HIGH RISK =================

    high_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        AND risk_level = 'High'
        """,
        (user_id,)
    ).fetchone()["count"]


    # ================= MODERATE RISK =================

    moderate_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        AND risk_level = 'Moderate'
        """,
        (user_id,)
    ).fetchone()["count"]


    # ================= LOW RISK =================

    low_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        AND risk_level = 'Low'
        """,
        (user_id,)
    ).fetchone()["count"]


    # ================= LATEST PREDICTION =================

    latest_prediction = connection.execute(
        """
        SELECT risk_level
        FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()


    # ================= PREDICTION HISTORY =================

    prediction_history = connection.execute(
        """
        SELECT
            daily_screen_time,
            prediction_date
        FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date ASC
        """,
        (user_id,)
    ).fetchall()


    connection.close()


    # ================= CHART DATA =================

    dates = []
    screen_times = []

    for row in prediction_history:

        dates.append(row["prediction_date"])

        screen_times.append(
            row["daily_screen_time"]
        )


    # ================= STATISTICS VALUES =================

    avg_screen_time = round(
        statistics["avg_screen_time"] or 0,
        2
    )

    max_screen_time = round(
        statistics["max_screen_time"] or 0,
        2
    )

    min_screen_time = round(
        statistics["min_screen_time"] or 0,
        2
    )


    # ================= LATEST RISK =================

    if latest_prediction:

        risk_level = latest_prediction["risk_level"]

    else:

        risk_level = "Not Available"


    # ================= RENDER ANALYTICS =================

    return render_template(
        "analytics.html",
        name=session["user_name"],
        total_predictions=total_predictions,
        avg_screen_time=avg_screen_time,
        max_screen_time=max_screen_time,
        min_screen_time=min_screen_time,
        high_risk=high_risk,
        moderate_risk=moderate_risk,
        low_risk=low_risk,
        risk_level=risk_level,
        dates=dates,
        screen_times=screen_times
    )

#=====================================================
#USER SETTINGS
#=====================================================

@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "settings.html",
        name=session["user_name"]
)

# =====================================================
# USER REPORTS
# =====================================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user_id = session["user_id"]

    total_predictions = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["count"]

    statistics = connection.execute(
        """
        SELECT
            AVG(daily_screen_time) AS avg_screen_time,
            MAX(daily_screen_time) AS max_screen_time,
            MIN(daily_screen_time) AS min_screen_time
        FROM predictions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    high_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        AND risk_level = 'High'
        """,
        (user_id,)
    ).fetchone()["count"]

    moderate_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        AND risk_level = 'Moderate'
        """,
        (user_id,)
    ).fetchone()["count"]

    low_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE user_id = ?
        AND risk_level = 'Low'
        """,
        (user_id,)
    ).fetchone()["count"]

    latest_prediction = connection.execute(
        """
        SELECT risk_level
        FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    avg_screen_time = round(
        statistics["avg_screen_time"] or 0,
        2
    )

    max_screen_time = round(
        statistics["max_screen_time"] or 0,
        2
    )

    min_screen_time = round(
        statistics["min_screen_time"] or 0,
        2
    )

    if latest_prediction:
        risk_level = latest_prediction["risk_level"]
    else:
        risk_level = "Not Available"

    return render_template(
        "reports.html",
        name=session["user_name"],
        total_predictions=total_predictions,
        avg_screen_time=avg_screen_time,
        max_screen_time=max_screen_time,
        min_screen_time=min_screen_time,
        high_risk=high_risk,
        moderate_risk=moderate_risk,
        low_risk=low_risk,
        risk_level=risk_level
    )

# =====================================================

# CHANGE PASSWORD

# =====================================================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    message = ""
    success = ""

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        if not check_password_hash(
            user["password"],
            current_password
        ):

            message = "Current password is incorrect."

        elif new_password != confirm_password:

            message = "New passwords do not match."

        elif len(new_password) < 6:

            message = "New password must contain at least 6 characters."

        else:

            hashed_password = generate_password_hash(
                new_password
            )

            connection.execute(
                """
                UPDATE users
                SET password = ?
                WHERE id = ?
                """,
                (
                    hashed_password,
                    session["user_id"]
                )
            )

            connection.commit()

            success = "Password changed successfully."

        connection.close()

    return render_template(
        "change_password.html",
        name=session["user_name"],
        message=message,
        success=success
    )

# =====================================================
# USER PREDICTION PAGE
# =====================================================

@app.route("/prediction")
def prediction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


# =====================================================
# USER PREDICTION
# =====================================================

@app.route("/predict", methods=["POST"])
def predict():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        # ==========================================
        # CSV PREDICTION
        # ==========================================

        if (
            "csv_file" in request.files
            and request.files["csv_file"].filename != ""
        ):

            file = request.files["csv_file"]

            df = pd.read_csv(file)

            required_columns = [
                "daily_screen_time",
                "social_media_time",
                "gaming_time",
                "night_screen_time",
                "weekend_screen_time"
            ]

            if not all(
                column in df.columns
                for column in required_columns
            ):

                return render_template(
                    "index.html",
                    error="Invalid CSV format. Please upload the correct usage report."
                )

            input_data = df[
                required_columns
            ].iloc[[0]]

        # ==========================================
        # MANUAL PREDICTION
        # ==========================================

        else:

            data = {

                "daily_screen_time": [
                    float(
                        request.form[
                            "daily_screen_time"
                        ]
                    )
                ],

                "social_media_time": [
                    float(
                        request.form[
                            "social_media_time"
                        ]
                    )
                ],

                "gaming_time": [
                    float(
                        request.form[
                            "gaming_time"
                        ]
                    )
                ],

                "night_screen_time": [
                    float(
                        request.form[
                            "night_screen_time"
                        ]
                    )
                ],

                "weekend_screen_time": [
                    float(
                        request.form[
                            "weekend_screen_time"
                        ]
                    )
                ]
            }

            input_data = pd.DataFrame(data)

        # ==========================================
        # ML PREDICTION
        # ==========================================

        prediction_result = model.predict(
            input_data
        )[0]

        probabilities = model.predict_proba(
            input_data
        )[0]

        confidence = round(
            max(probabilities) * 100,
            2
        )

        # ==========================================
        # GET VALUES
        # ==========================================

        daily_screen_time = float(
            input_data[
                "daily_screen_time"
            ].iloc[0]
        )

        social_media_time = float(
            input_data[
                "social_media_time"
            ].iloc[0]
        )

        gaming_time = float(
            input_data[
                "gaming_time"
            ].iloc[0]
        )

        night_screen_time = float(
            input_data[
                "night_screen_time"
            ].iloc[0]
        )

        weekend_screen_time = float(
            input_data[
                "weekend_screen_time"
            ].iloc[0]
        )

        # ==========================================
        # SAVE PREDICTION
        # ==========================================

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO predictions (
                user_id,
                age,
                daily_screen_time,
                social_media_time,
                gaming_time,
                study_work_time,
                phone_unlocks,
                night_screen_time,
                sleep_duration,
                physical_activity,
                breaks_per_day,
                weekend_screen_time,
                risk_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                None,
                daily_screen_time,
                social_media_time,
                gaming_time,
                None,
                None,
                night_screen_time,
                None,
                None,
                None,
                weekend_screen_time,
                prediction_result
            )
        )

        connection.commit()

        connection.close()

        return render_template(
            "result.html",
            prediction=prediction_result,
            confidence=confidence
        )

    except Exception as e:

        return render_template(
            "index.html",
            error=f"Error: {str(e)}"
        )


# =====================================================
#                    ADMIN SECTION
# =====================================================


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    total_users = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        """
    ).fetchone()["count"]

    total_predictions = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        """
    ).fetchone()["count"]

    high_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'High'
        """
    ).fetchone()["count"]

    moderate_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'Moderate'
        """
    ).fetchone()["count"]

    low_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'Low'
        """
    ).fetchone()["count"]

    users = connection.execute(
        """
        SELECT id, name, email
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        name=session["admin_name"],
        total_users=total_users,
        total_predictions=total_predictions,
        high_risk=high_risk,
        moderate_risk=moderate_risk,
        low_risk=low_risk,
        users=users
    )


# =====================================================
# ADMIN USERS
# =====================================================

@app.route("/admin/users")
def admin_users():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    users = connection.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            COUNT(p.id) AS prediction_count,
            MAX(p.prediction_date) AS last_prediction
        FROM users u
        LEFT JOIN predictions p
        ON u.id = p.user_id
        GROUP BY u.id
        ORDER BY u.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_users.html",
        name=session["admin_name"],
        users=users
    )


# =====================================================
# ADMIN PREDICTIONS
# =====================================================

@app.route("/admin/predictions")
def admin_predictions():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    predictions = connection.execute(
        """
        SELECT
            p.user_id,
            u.name AS user_name,
            p.daily_screen_time,
            p.social_media_time,
            p.gaming_time,
            p.night_screen_time,
            p.weekend_screen_time,
            p.risk_level,
            p.prediction_date
        FROM predictions p
        JOIN users u
        ON p.user_id = u.id
        ORDER BY p.prediction_date DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_predictions.html",
        name=session["admin_name"],
        predictions=predictions
    )


# =====================================================
# ADMIN REPORTS
# =====================================================

@app.route("/admin/reports")
def admin_reports():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    total_users = connection.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]

    total_predictions = connection.execute(
        "SELECT COUNT(*) AS count FROM predictions"
    ).fetchone()["count"]

    high_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'High'
        """
    ).fetchone()["count"]

    moderate_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'Moderate'
        """
    ).fetchone()["count"]

    low_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'Low'
        """
    ).fetchone()["count"]

    statistics = connection.execute(
        """
        SELECT
            AVG(daily_screen_time) AS avg_screen_time,
            MAX(daily_screen_time) AS max_screen_time,
            MIN(daily_screen_time) AS min_screen_time,
            AVG(social_media_time) AS avg_social_media,
            AVG(gaming_time) AS avg_gaming,
            AVG(night_screen_time) AS avg_night_usage
        FROM predictions
        """
    ).fetchone()

    connection.close()

    return render_template(
        "admin_reports.html",
        name=session["admin_name"],
        total_users=total_users,
        total_predictions=total_predictions,
        high_risk=high_risk,
        moderate_risk=moderate_risk,
        low_risk=low_risk,

        avg_screen_time=round(
            statistics["avg_screen_time"] or 0,
            2
        ),

        max_screen_time=round(
            statistics["max_screen_time"] or 0,
            2
        ),

        min_screen_time=round(
            statistics["min_screen_time"] or 0,
            2
        ),

        avg_social_media=round(
            statistics["avg_social_media"] or 0,
            2
        ),

        avg_gaming=round(
            statistics["avg_gaming"] or 0,
            2
        ),

        avg_night_usage=round(
            statistics["avg_night_usage"] or 0,
            2
        )
    )


# =====================================================
# ADMIN PDF REPORT
# =====================================================

@app.route("/admin/reports/pdf")
def admin_reports_pdf():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import inch
    from io import BytesIO
    from datetime import datetime

    connection = get_db_connection()

    total_users = connection.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]

    total_predictions = connection.execute(
        "SELECT COUNT(*) AS count FROM predictions"
    ).fetchone()["count"]

    high_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'High'
        """
    ).fetchone()["count"]

    moderate_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'Moderate'
        """
    ).fetchone()["count"]

    low_risk = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM predictions
        WHERE risk_level = 'Low'
        """
    ).fetchone()["count"]

    statistics = connection.execute(
        """
        SELECT
            AVG(daily_screen_time) AS avg_screen_time,
            MAX(daily_screen_time) AS max_screen_time,
            MIN(daily_screen_time) AS min_screen_time,
            AVG(social_media_time) AS avg_social_media,
            AVG(gaming_time) AS avg_gaming,
            AVG(night_screen_time) AS avg_night_usage
        FROM predictions
        """
    ).fetchone()

    connection.close()

    avg_screen_time = round(
        statistics["avg_screen_time"] or 0,
        2
    )

    max_screen_time = round(
        statistics["max_screen_time"] or 0,
        2
    )

    min_screen_time = round(
        statistics["min_screen_time"] or 0,
        2
    )

    avg_social_media = round(
        statistics["avg_social_media"] or 0,
        2
    )

    avg_gaming = round(
        statistics["avg_gaming"] or 0,
        2
    )

    avg_night_usage = round(
        statistics["avg_night_usage"] or 0,
        2
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=25
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10
    )

    story = []

    story.append(
        Paragraph(
            "ScreenSense AI",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Screen-Time Risk Analysis Report",
            subtitle_style
        )
    )

    report_date = datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    story.append(
        Paragraph(
            f"<b>Report Generated:</b> {report_date}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    # ---------------- OVERALL STATISTICS ----------------

    story.append(
        Paragraph(
            "Overall Statistics",
            heading_style
        )
    )

    overall_data = [
        ["Metric", "Value"],
        ["Total Registered Users", str(total_users)],
        ["Total Predictions", str(total_predictions)],
        ["High Risk Predictions", str(high_risk)],
        ["Moderate Risk Predictions", str(moderate_risk)],
        ["Low Risk Predictions", str(low_risk)]
    ]

    overall_table = Table(
        overall_data,
        colWidths=[
            3.8 * inch,
            2 * inch
        ]
    )

    overall_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#641333")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(overall_table)

    # ---------------- USAGE STATISTICS ----------------

    story.append(
        Paragraph(
            "Usage Statistics",
            heading_style
        )
    )

    usage_data = [
        ["Metric", "Average / Value"],

        [
            "Average Daily Screen Time",
            f"{avg_screen_time} hours"
        ],

        [
            "Average Social Media Usage",
            f"{avg_social_media} hours"
        ],

        [
            "Average Gaming Usage",
            f"{avg_gaming} hours"
        ],

        [
            "Average Night Usage",
            f"{avg_night_usage} hours"
        ],

        [
            "Highest Screen Time",
            f"{max_screen_time} hours"
        ],

        [
            "Lowest Screen Time",
            f"{min_screen_time} hours"
        ]
    ]

    usage_table = Table(
        usage_data,
        colWidths=[
            3.8 * inch,
            2 * inch
        ]
    )

    usage_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#641333")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(usage_table)

    # ---------------- RISK DISTRIBUTION ----------------

    story.append(
        Paragraph(
            "Risk Distribution",
            heading_style
        )
    )

    risk_data = [
        ["Risk Level", "Number of Predictions"],
        ["High", str(high_risk)],
        ["Moderate", str(moderate_risk)],
        ["Low", str(low_risk)]
    ]

    risk_table = Table(
        risk_data,
        colWidths=[
            3.8 * inch,
            2 * inch
        ]
    )

    risk_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#641333")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(risk_table)

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "This report provides a summary of screen-time "
            "predictions recorded in the ScreenSense AI system.",
            styles["Normal"]
        )
    )

    document.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="ScreenSense_AI_Report.pdf",
        mimetype="application/pdf"
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
