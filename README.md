# SpendSquad

SpendSquad is a machine learning-powered personal finance management system that helps users track expenses, predict future spending patterns, manage budgets, and monitor savings goals.

## Overview

The application combines expense tracking with predictive analytics to provide users with insights into their spending habits and future expenses.

## Features

* Add and manage expenses
* Automatic expense categorization
* Monthly expense reports
* Budget planning and monitoring
* Savings goal tracking
* Expense prediction using machine learning
* Interactive web-based dashboard

## Technologies Used

* Python
* Flask
* MySQL
* Pandas
* Scikit-learn
* HTML
* CSS

## Machine Learning Models

### Random Forest

* Automatic expense category prediction based on transaction descriptions
* TF-IDF text vectorization for processing expense descriptions

### Linear Regression

* Forecasting future expenses for different spending categories
* Monthly expense trend prediction

## Project Structure

```text
project/
├── app.py
├── expense.py
├── main.py
├── random_forest_model.pkl
├── tfidf_vectorizer.pkl
├── templates/
├── static/
└── requirements.txt
```

## Installation

1. Clone the repository

```bash
git clone <repository-url>
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with database credentials

4. Run the application

```bash
python app.py
```

## Future Enhancements

* User authentication
* Interactive data visualizations
* Cloud deployment
* Mobile-responsive design
* Advanced financial analytics

## Academic Project

This project was developed as a collaborative academic mini-project to explore machine learning applications in personal finance management.
