import pandas as pd
import numpy as np
import pymysql
from sklearn.linear_model import LinearRegression

class ExpensePredictor:
    def __init__(self, db_config):
        self.db_config = db_config
        self.models = {}  # Dictionary to store trained models
        self.df = None  # Placeholder for the dataset
        self._load_data()
        self._train_models()

    def _connect_db(self):
        """Establishes a database connection."""
        return pymysql.connect(**self.db_config)

    def _load_data(self):
        """Fetches data from the MyExpense table and processes it."""
        conn = self._connect_db()
        cursor = conn.cursor()
        query = "SELECT Month, Category, Total_Expense FROM MyExpense"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to DataFrame
        self.df = pd.DataFrame(data, columns=["Month", "Category", "Total_Expense"])

        # Convert Month to numerical values
        self.df["Month"] = pd.to_datetime(self.df["Month"], errors="coerce")
        self.df.dropna(subset=["Month"], inplace=True)
        self.df["Month_Num"] = self.df["Month"].dt.strftime("%Y%m").astype(int)
        self.df["Total_Expense"] = self.df["Total_Expense"].astype(float)

    def _train_models(self):
        """Trains a linear regression model for each category."""
        categories = self.df["Category"].unique()
        for category in categories:
            df_cat = self.df[self.df["Category"] == category].copy()
            df_cat = df_cat.sort_values(by="Month_Num")
            X = df_cat[["Month_Num"]].values
            y = df_cat["Total_Expense"].values
            
            model = LinearRegression()
            model.fit(X, y)
            self.models[category] = model
        
        print("\n✅ Models trained successfully.")

    def predict_expense(self, category, year, month):
        """Predicts expense for a given category & date using trained model."""
        if category not in self.models:
            return f"❌ No trained model found for category: {category}"
        
        model = self.models[category]
        input_month = int(f"{year}{month:02d}")
        predicted_expense = model.predict([[input_month]])[0]
        
        return f"✅ Predicted {category} expense for {year}-{month}: ${round(predicted_expense, 2)}"
    
    def add_expense(self, month, category, total_expense):
        """Adds a new expense entry to the MyExpense table."""
        conn = self._connect_db()
        cursor = conn.cursor()
        query = "INSERT INTO MyExpense (Month, Category, Total_Expense) VALUES (%s, %s, %s)"
        cursor.execute(query, (month, category, total_expense))
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Expense added successfully.")
    def get_total_expense_summary(self, month):
        """Fetches the total expense per category for a given month."""
        conn = self._connect_db()
        cursor = conn.cursor()
    
    # SQL query to sum expenses by category for the given month
        query = """
        SELECT Category, SUM(CAST(Total_Expense AS DECIMAL(10,2))) as Total_Spent 
        FROM MyExpense 
        WHERE Month = %s 
        GROUP BY Category
        """
    
        cursor.execute(query, (month,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()

    # Convert result to DataFrame
        df_summary = pd.DataFrame(data, columns=["Category", "Total_Spent"])
        return df_summary