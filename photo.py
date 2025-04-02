from flask import Flask, render_template
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

# Load Excel data
df = pd.read_excel("pro_duct.xlsx", dtype={"image": str})
df.fillna("", inplace=True)  # Fill NaN with empty strings

# Encode categorical data
label_encoder = LabelEncoder()
df["category_encoded"] = label_encoder.fit_transform(df["category"])

# Generate additional features for training
df["seasonal_factor"] = np.random.uniform(0.85, 1.15, len(df))
df["market_demand"] = np.random.uniform(0.75, 1.25, len(df))

# Store predicted prices
predicted_prices = []

# Train a separate model for each category
category_models = {}

for category in df["category"].unique():
    category_df = df[df["category"] == category].copy()
    
    # Generate training data within the category
    train_size = len(category_df)
    train_data = pd.DataFrame({
        "price": np.random.uniform(category_df["price"].min(), category_df["price"].max(), train_size),
        "seasonal_factor": np.random.uniform(0.85, 1.15, train_size),
        "market_demand": np.random.uniform(0.75, 1.25, train_size)
    })
    
    # Generate target prices (simulate real-world fluctuations)
    train_data["predicted_price"] = train_data["price"] * train_data["seasonal_factor"] * train_data["market_demand"]

    # Train model for this category
    X_train = train_data[["price", "seasonal_factor", "market_demand"]]
    y_train = train_data["predicted_price"]

    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)

    # Save trained model for this category
    category_models[category] = model

    # Predict prices for this category
    X_test = category_df[["price", "seasonal_factor", "market_demand"]]
    category_df["predicted_price"] = model.predict(X_test)
    category_df["predicted_price"] = category_df["predicted_price"].round(2)

    predicted_prices.append(category_df)

# Combine results back into a single DataFrame
df_predicted = pd.concat(predicted_prices)

# Convert DataFrame to dictionary format for rendering in HTML
products = df.to_dict(orient="records")
predicted_products = df_predicted.to_dict(orient="records")

@app.route('/')
def original_products():
    return render_template("original.html", products=products)

@app.route('/predicted')
def predicted_products_page():
    return render_template("duplicate.html", products=predicted_products)

if __name__ == "__main__":
    app.run(debug=True)
