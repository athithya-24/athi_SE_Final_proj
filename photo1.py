from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Load data from Excel
df = pd.read_excel("pro_duct.xlsx")

# Convert DataFrame to list of dictionaries
products = df.to_dict(orient="records")

@app.route("/")
def product_list():
    return render_template("index11.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)
