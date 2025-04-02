import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# Sample dataset
data = {
    "demand": [100, 200, 150, 300, 250, 180, 130, 220, 270, 310],
    "season": [1, 2, 1, 3, 2, 3, 1, 2, 3, 1],
    "price": [500, 800, 650, 1200, 1000, 900, 550, 950, 1100, 1300]
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Features (X) and Target (y)
X = df[["demand", "season"]]
y = df["price"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, "price_1.pkl")

print("Price prediction model saved as price_model.pkl!")
