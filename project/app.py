from flask import Flask, render_template, request, jsonify,redirect, url_for, flash
from expense import ExpensePredictor
import pandas as pd
import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Load the model and vectorizer from files
rf_model = joblib.load('random_forest_model.pkl')
vectorizer = joblib.load('tfidf_vectorizer.pkl')

import re
import string
# Preprocessing function (same as in your notebook)
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = text.strip()
    return text

# Prediction function using the trained Random Forest model
def predict_expense_category(description):
    cleaned_desc = preprocess_text(description)
    desc_vectorized = vectorizer.transform([cleaned_desc])
    predicted_category = rf_model.predict(desc_vectorized)[0]
    return predicted_category

@app.route('/load', methods=['GET', 'POST'])
def load():
    """Handles user input for adding expenses to the database."""
    if request.method == 'POST':
        month = request.form.get("date")
        amount = request.form.get("amount")
        description = request.form.get("description")

        if not month or not amount or not description:
            return render_template("load.html", message="❌ Please fill all fields.")

        # Predict category from the description
        predicted_category = predict_expense_category(description)

        # Establish a database connection
        conn = get_db_connection()
        if conn:
            try:
                # Add the expense to the database
                cursor = conn.cursor()
                cursor.execute("INSERT INTO MyExpense (Month,Total_Expense, Category) VALUES (%s, %s, %s)", 
                               (month, float(amount), predicted_category))
                conn.commit()

                return render_template("load.html", message=f"✅ Expense added with category: {predicted_category}!")
            except Exception as e:
                return render_template("load.html", message=f"❌ Error: {str(e)}")
            finally:
                conn.close()  # Always close the connection after use

    return render_template('load.html', message="")


expense_predictor = ExpensePredictor(DB_CONFIG)
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        year = request.form.get("year", type=int)
        month = request.form.get("month", type=int)

        if not year or not month:
            return jsonify({"error": "Missing required parameters"}), 400

        # Get all categories from the trained models
        categories = list(expense_predictor.models.keys())

        predictions = {}
        for category in categories:
            predicted_expense = expense_predictor.predict_expense(category, year, month)
            predictions[category] = predicted_expense

        return render_template("predict.html", predictions=predictions, year=year, month=month)

    return render_template("predict.html", predictions=None)


def get_db_connection():
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        print(f"Database connection error: {e}")
        return None
    
@app.route('/report', methods=['GET'])
def report():
    # Get the user input for year and month, with default values in case they're not provided
    selected_year = request.args.get('year', '2025')  # Default year for testing if not provided by user
    selected_month = request.args.get('month', '03')  # Default month for testing if not provided by user

    # SQL query to fetch the total expense per category for the selected year and month
    query = """
    SELECT Category, SUM(CAST(Total_EXPENSE AS DECIMAL(10,2))) AS Total_Expense
    FROM MyExpense
    WHERE YEAR(Month) = %s AND MONTH(Month) = %s
    GROUP BY Category;
    """

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (selected_year, selected_month))
                report_data = cursor.fetchall()
        finally:
            conn.close()

        # Debugging: Check the retrieved data
        print("DEBUG: Report Data ->", report_data)

        return render_template('report.html', report_data=report_data, selected_year=selected_year, selected_month=selected_month)

    return "Database connection error", 500




@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    if not data or "date" not in data or "category" not in data or "amount" not in data:
        return jsonify({"error": "Missing required parameters"}), 400

    expense_predictor.add_expense(data["date"], data["category"], data["amount"])
    return jsonify({"message": "Expense added successfully"})


@app.route("/budget", methods=["GET", "POST"])
def budget():
    if request.method == "POST":
        month = int(request.form["month"])
        year = int(request.form["year"])
        budget_amount = float(request.form["budget_amount"])

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Budget (month, year, budget_amount) 
                        VALUES (%s, %s, %s) 
                        ON DUPLICATE KEY UPDATE budget_amount = VALUES(budget_amount)
                    """, (month, year, budget_amount))
                    conn.commit()
                    message = "✅ BUDGET SAVED SUCCESSFULLY!"
                    cursor.execute("""
                        SELECT SUM(amount) FROM Expense WHERE MONTH(date) = %s AND YEAR(date) = %s
                    """, (month, year))
                    total_expense = cursor.fetchone()["SUM(amount)"] or 0

                    print(f"Total Expense: {total_expense}, Budget: {budget_amount}")  # Debugging

                    if total_expense >= 0.8 * budget_amount:
                        flash("⚠️ Warning: Your expenses have reached 80% of your budget!", "warning")
                        print("Flash warning triggered!")  # Debugging

                flash("✅ Budget saved successfully!", "success")
                print("Flash success triggered!")  # Debugging

            except Exception as e:
                conn.rollback()
                flash(f"❌ Error: {e}", "danger")

            finally:
                conn.close()

        return redirect(url_for("budget"))

    return render_template("budget.html")



@app.route("/goal", methods=["GET", "POST"])
def goal():
    if request.method == "POST":
        month = int(request.form["month"])
        year = int(request.form["year"])
        goal_amount = float(request.form["goal_amount"])

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Goal (month, year, goal_amount, status) 
                        VALUES (%s, %s, %s, 'Pending') 
                        ON DUPLICATE KEY UPDATE goal_amount = VALUES(goal_amount), status = 'Pending'
                    """, (month, year, goal_amount))
                    conn.commit()

                    cursor.execute("""
                        SELECT SUM(amount) FROM MyExpense WHERE MONTH(date) = %s AND YEAR(date) = %s
                    """, (month, year))
                    total_expense = cursor.fetchone()["SUM(amount)"] or 0

                    if total_expense <= goal_amount:
                        cursor.execute("""
                            UPDATE Goal SET status = 'Achieved' WHERE month = %s AND year = %s
                        """, (month, year))
                        conn.commit()
                        flash("🎉 Congratulations! You have achieved your savings goal!", "success")

                        savings_percentage = ((goal_amount - total_expense) / goal_amount) * 100
                        badge = "No Badge"
                        if savings_percentage >= 50:
                            badge = "🏆 Gold Saver!"
                        elif savings_percentage >= 30:
                            badge = "🥈 Silver Saver!"
                        elif savings_percentage >= 10:
                            badge = "🥉 Bronze Saver!"

                        if badge != "No Badge":
                            flash(f"You earned a {badge} for your savings this month! 🚀", "info")

                flash("✅ Goal saved successfully!", "success")

            except Exception as e:
                conn.rollback()
                flash(f"❌ Error: {e}", "danger")

            finally:
                conn.close()

        return redirect(url_for("goal"))

    return render_template("goal.html")


    
if __name__ == "__main__":
    app.run(debug=True, port=5000)
