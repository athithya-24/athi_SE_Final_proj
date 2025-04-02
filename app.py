from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure SQLite database inside the venv
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Create a simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Create the database using app context
with app.app_context():
    db.create_all()
    print("Database and tables created!")

@app.route('/')
def home():
    return "SQLite Database Created Successfully!"

if __name__ == '__main__':
    app.run(debug=True)
