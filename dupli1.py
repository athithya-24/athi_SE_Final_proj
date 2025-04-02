from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import joblib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products5.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the ML model
price_model = joblib.load("zen_model1.pkl")

# Define Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    demand = db.Column(db.Integer, default=100)
    season = db.Column(db.Integer, default=1)

# Insert initial data
def insert_initial_data():
    with app.app_context():
        if Product.query.first() is None:
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
            product.price = round(new_price, 2)  
        db.session.commit()
        print("Prices updated successfully!")

# Route to display original prices
@app.route('/original')
def original():
    products = Product.query.all()
    return render_template('original.html', products=products)

# Route to display updated prices
@app.route('/store')
def store():
    update_prices()
    products = Product.query.all()
    return render_template('duplicate.html', products=products)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        insert_initial_data()
    app.run(debug=True)
