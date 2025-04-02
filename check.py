from dpp2 import Product, db, app  # Import app to set up the application context

with app.app_context():  # Set up Flask application context
    all_products = Product.query.all()
    print(f"Total products in DB: {len(all_products)}")
