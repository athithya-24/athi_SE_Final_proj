from flask import Flask, render_template
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

# Load Excel data
df = pd.read_excel("pro_duct.xlsx", dtype={"image": str})
df.fillna("", inplace=True)  # Fill NaN values with empty strings

# Encode categorical data
label_encoder = LabelEncoder()
df["category_encoded"] = label_encoder.fit_transform(df["category"])

# Store predicted prices
predicted_prices = []
category_models = {}

# Train a separate model for each category
for category in df["category"].unique():
    category_df = df[df["category"] == category].copy()
    
    # Define category-based adjustments
    if "electronics" in category.lower():
        seasonal_range = (0.98, 1.02)  # Almost stable
        demand_range = (0.95, 1.05)  # Minimal market demand variation
    elif "fashion" in category.lower():
        seasonal_range = (0.70, 1.30)  # Fashion has high seasonal variation
        demand_range = (0.85, 1.25)
    elif "luxury" in category.lower():
        seasonal_range = (0.95, 1.05)  # Stable pricing
        demand_range = (0.90, 1.10)
    else:
        seasonal_range = (0.85, 1.15)  # Default case
        demand_range = (0.75, 1.25)
    
    # Generate training data with category-specific variations
    train_size = len(category_df)
    train_data = pd.DataFrame({
        "price": category_df["price"],  # Use actual prices, no artificial range
        "seasonal_factor": np.random.uniform(*seasonal_range, train_size),
        "market_demand": np.random.uniform(*demand_range, train_size)
    })
    
    # Generate predicted price using a controlled formula
    train_data["predicted_price"] = train_data["price"] * (
        0.7 + 0.3 * train_data["seasonal_factor"] * train_data["market_demand"]
    )  # Weighted approach to reduce impact

    # Train the model for this category
    X_train = train_data[["price", "seasonal_factor", "market_demand"]]
    y_train = train_data["predicted_price"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    # Save trained model
    category_models[category] = model

    # Predict prices for this category
    X_test = category_df[["price"]].copy()
    X_test["seasonal_factor"] = np.random.uniform(*seasonal_range, len(X_test))
    X_test["market_demand"] = np.random.uniform(*demand_range, len(X_test))

    category_df["predicted_price"] = model.predict(X_test)
    
    # Clip extreme values to ensure reasonable predictions
    category_df["predicted_price"] = np.clip(category_df["predicted_price"], 
                                             category_df["price"] * 0.8, 
                                             category_df["price"] * 1.5)
    
    category_df["predicted_price"] = category_df["predicted_price"].round(2)

    predicted_prices.append(category_df)

# Merge all predictions into a single DataFrame
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
