from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import joblib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products1.db'  # Corrected DB name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the ML model
price_model = joblib.load("price_model.pkl")

# Define Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    demand = db.Column(db.Integer, default=100)  # Demand factor
    season = db.Column(db.Integer, default=1)  # Season factor

# Function to insert initial data
def insert_initial_data():
    with app.app_context():
        if Product.query.first() is None:  # Check if DB is empty
            sample_products = [
                Product(name="Book A", category="Book", price=200, demand=150, season=1),
                Product(name="Book B", category="Book", price=250, demand=120, season=2),
                Product(name="Football", category="Sport", price=500, demand=180, season=3),
                Product(name="Badminton Racket", category="Sport", price=750, demand=130, season=2)
            ]
            db.session.add_all(sample_products)
            db.session.commit()
            print("Sample data inserted successfully!")

# Function to update prices using ML
def update_prices():
    with app.app_context():
        products = Product.query.all()
        for product in products:
            new_price = price_model.predict([[product.demand, product.season]])[0]
            product.price = round(new_price, 2)  # Update price in DB
        db.session.commit()
        print("Prices updated successfully!")

# Store Route
@app.route('/store')
def store():
    update_prices()  # Update prices before rendering the page
    products = Product.query.all()
    return render_template('duplicatestore.html', products=products)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database if not exists
        insert_initial_data()  # Insert sample data
    app.run(debug=True)
