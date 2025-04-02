from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app
app = Flask(__name__)

# SQLite Database Configuration
db_path = os.path.join(os.path.abspath(os.getcwd()), 'test.db')  # Creating a test database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test_secret_key'

# Initialize Database
db = SQLAlchemy(app)

# Define User Model
class User1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)

# Create Database and Insert Test Data
with app.app_context():
    db.create_all()  # Create table if not exists

    # Insert a test user if not exists
    if not User.query.filter_by(username='test_user').first():
        new_user = User(username='test_user')
        db.session.add(new_user)
        db.session.commit()
        print("✅ Test user added to the database.")
    else:
        print("ℹ️ Test user already exists.")

    # Retrieve and print all users
    users = User.query.all()
    print("📌 Users in database:")
    for user in users:
        print(f"- ID: {user.id}, Username: {user.username}")
