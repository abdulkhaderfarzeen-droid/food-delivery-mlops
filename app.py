from flask import Flask, render_template, request, redirect, url_for, flash, session

import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

import re
import joblib
import numpy as np
import pandas as pd


app = Flask(__name__)

app.secret_key = '9945'


# ============================================================
# LOAD MACHINE LEARNING MODEL
# ============================================================

model = joblib.load("delivery_time1_model.pkl")
scaler = joblib.load("scaler1.pkl")


# ============================================================
# SQLITE DATABASE CONNECTION
# ============================================================

def get_db_connection():
    conn = sqlite3.connect("food.db")
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# CREATE DATABASE TABLE
# ============================================================

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            u_id INTEGER PRIMARY KEY AUTOINCREMENT,
            u_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


# ============================================================
# ABOUT PAGE
# ============================================================

@app.route('/about')
def about():
    return render_template('about.html')


# ============================================================
# METHODOLOGY PAGE
# ============================================================

@app.route('/methodology')
def methodology():
    return render_template('methodology.html')


# ============================================================
# PREDICTION PAGE
# ============================================================

@app.route('/predict', methods=['GET', 'POST'])
def predict():

    # Check whether user is logged in
    if 'user_id' not in session:
        flash(
            "Please login to access the prediction system",
            "warning"
        )
        return redirect(url_for('register'))

    prediction = None

    if request.method == "POST":

        # ----------------------------------------------------
        # Get values from HTML form
        # ----------------------------------------------------

        Distance_km = float(
            request.form['Distance_km']
        )

        Traffic_Level = request.form['Traffic_Level']

        Preparation_Time_min = int(
            request.form['Preparation_Time_min']
        )

        Courier_Experience_yrs = int(
            request.form['Courier_Experience_yrs']
        )

        weather = request.form['Weather']

        time_of_day = request.form['Time_of_Day']

        vehicle = request.form['Vehicle_Type']


        # ----------------------------------------------------
        # WEATHER ENCODING
        # ----------------------------------------------------

        Weather_Clear = 1 if weather == "clear" else 0
        Weather_Foggy = 1 if weather == "foggy" else 0
        Weather_Rainy = 1 if weather == "rainy" else 0
        Weather_Snowy = 1 if weather == "snowy" else 0
        Weather_Windy = 1 if weather == "windy" else 0


        # ----------------------------------------------------
        # TIME OF DAY ENCODING
        # ----------------------------------------------------

        Time_of_Day_Morning = (
            1 if time_of_day == "morning" else 0
        )

        Time_of_Day_Afternoon = (
            1 if time_of_day == "afternoon" else 0
        )

        Time_of_Day_Evening = (
            1 if time_of_day == "evening" else 0
        )

        Time_of_Day_Night = (
            1 if time_of_day == "night" else 0
        )


        # ----------------------------------------------------
        # VEHICLE TYPE ENCODING
        # ----------------------------------------------------

        Vehicle_Type_Bike = (
            1 if vehicle == "bike" else 0
        )

        Vehicle_Type_Car = (
            1 if vehicle == "car" else 0
        )

        Vehicle_Type_Scooter = (
            1 if vehicle == "scooter" else 0
        )


        # ----------------------------------------------------
        # CREATE FEATURES
        # ----------------------------------------------------

        order_features = {

            "Distance_km": Distance_km,

            "Traffic_Level": Traffic_Level,

            "Preparation_Time_min": Preparation_Time_min,

            "Courier_Experience_yrs": Courier_Experience_yrs,

            "Weather_Clear": Weather_Clear,

            "Weather_Foggy": Weather_Foggy,

            "Weather_Rainy": Weather_Rainy,

            "Weather_Snowy": Weather_Snowy,

            "Weather_Windy": Weather_Windy,

            "Time_of_Day_Afternoon":
                Time_of_Day_Afternoon,

            "Time_of_Day_Evening":
                Time_of_Day_Evening,

            "Time_of_Day_Morning":
                Time_of_Day_Morning,

            "Time_of_Day_Night":
                Time_of_Day_Night,

            "Vehicle_Type_Bike":
                Vehicle_Type_Bike,

            "Vehicle_Type_Car":
                Vehicle_Type_Car,

            "Vehicle_Type_Scooter":
                Vehicle_Type_Scooter
        }


        # ----------------------------------------------------
        # CREATE DATAFRAME
        # ----------------------------------------------------

        order_df = pd.DataFrame(
            [order_features]
        )


        # ----------------------------------------------------
        # SCALE FEATURES
        # ----------------------------------------------------

        test_scaled = scaler.transform(
            order_df
        )


        # ----------------------------------------------------
        # ML MODEL PREDICTION
        # ----------------------------------------------------

        prediction = model.predict(
            test_scaled
        )[0]

        prediction = round(
            float(prediction),
            2
        )


        # ----------------------------------------------------
        # CONVERT MINUTES INTO HOURS + MINUTES
        # ----------------------------------------------------

        hours = int(
            prediction // 60
        )

        minutes = int(
            prediction % 60
        )


        if hours > 0:

            formatted_time = (
                f"{hours} hr {minutes} min"
            )

        else:

            formatted_time = (
                f"{minutes} min"
            )


        return render_template(
            'predict.html',
            prediction=formatted_time
        )


    return render_template(
        'predict.html',
        prediction=prediction
    )


# ============================================================
# LOGIN
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']


        # ----------------------------------------------------
        # EMAIL VALIDATION
        # ----------------------------------------------------

        if not re.match(
            r"[^@]+@[^@]+\.[^@]+",
            email
        ):

            flash(
                "Invalid email format",
                "danger"
            )

            return redirect(
                url_for('login')
            )


        # ----------------------------------------------------
        # PASSWORD VALIDATION
        # ----------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters",
                "danger"
            )

            return redirect(
                url_for('login')
            )


        # ----------------------------------------------------
        # CONNECT TO SQLITE
        # ----------------------------------------------------

        conn = get_db_connection()

        cursor = conn.cursor()


        # ----------------------------------------------------
        # FIND USER
        # ----------------------------------------------------

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()


        cursor.close()

        conn.close()


        # ----------------------------------------------------
        # CHECK PASSWORD
        # ----------------------------------------------------

        if user and check_password_hash(
            user['password'],
            password
        ):

            session['user_id'] = user['u_id']

            session['username'] = user['u_name']

            return redirect(
                url_for('index')
            )


        else:

            flash(
                "Invalid email or password",
                "danger"
            )

            return redirect(
                url_for('login')
            )


    return render_template(
        'login.html'
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(
        url_for('login')
    )


# ============================================================
# REGISTER
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        u_name = request.form['u_name']

        email = request.form['email']

        password = request.form['password']


        # ----------------------------------------------------
        # USERNAME VALIDATION
        # ----------------------------------------------------

        if not u_name.strip():

            flash(
                "Username is required",
                "danger"
            )

            return redirect(
                url_for('register')
            )


        # ----------------------------------------------------
        # EMAIL VALIDATION
        # ----------------------------------------------------

        if not re.match(
            r"[^@]+@[^@]+\.[^@]+",
            email
        ):

            flash(
                "Invalid email format",
                "danger"
            )

            return redirect(
                url_for('register')
            )


        # ----------------------------------------------------
        # PASSWORD VALIDATION
        # ----------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters",
                "danger"
            )

            return redirect(
                url_for('register')
            )


        # ----------------------------------------------------
        # CONNECT TO SQLITE
        # ----------------------------------------------------

        conn = get_db_connection()

        cursor = conn.cursor()


        # ----------------------------------------------------
        # CHECK WHETHER EMAIL ALREADY EXISTS
        # ----------------------------------------------------

        cursor.execute(
            "SELECT u_id FROM users WHERE email = ?",
            (email,)
        )


        if cursor.fetchone():

            flash(
                "Email already registered",
                "danger"
            )

            cursor.close()

            conn.close()

            return redirect(
                url_for('register')
            )


        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )


        # ----------------------------------------------------
        # INSERT USER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO users
            (u_name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                u_name,
                email,
                hashed_password
            )
        )


        conn.commit()


        cursor.close()

        conn.close()


        flash(
            "Registration successful. Please login.",
            "success"
        )


        return redirect(
            url_for('login')
        )


    return render_template(
        'register.html'
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == '__main__':

    # Create SQLite database and table
    init_db()

    # Start Flask
    app.run(
        host='0.0.0.0',
        port=4000,
        debug=False
    )