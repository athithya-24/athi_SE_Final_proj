from flask import Flask, render_template
import pandas as pd
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///product10.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Route to insert data from CSV
@app.route('/upload_csv')
def upload_csv():
    file_path = "products.csv"  # Ensure the file is in the correct path
    df = pd.read_csv(file_path, delimiter='\t')  # Adjust delimiter if needed

    # Insert data into the database
    for _, row in df.iterrows():
        if not Product.query.get(row['id']):  # Prevent duplicate entries
            product = Product(
                id=row['id'],
                category=row['category'],
                name=row['name'],
                price=row['price']
            )
            db.session.add(product)
    db.session.commit()
    return "CSV data inserted successfully!"

# Route to display the homepage (updated to `index1.html`)
@app.route('/')
def home():
    return render_template('index1.html')

# Route to display products in an HTML page
@app.route('/products')
def display_products():
    products = Product.query.all()
    return render_template('products.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)
