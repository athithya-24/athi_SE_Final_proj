from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
import os
import re  # For password validation

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key_here_123'

# Database Setup
db_path = os.path.join(os.path.abspath(os.getcwd()), 'user_auth.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) 
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER') or app.config['MAIL_USERNAME']

# Print to check if environment variables are being read correctly
print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
print("MAIL_DEFAULT_SENDER:", app.config['MAIL_DEFAULT_SENDER'])

mail = Mail(app)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Password Validation Function
def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[@$!%*?&]", password):
        return "Password must contain at least one special character."
    return None  # No errors

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Password Validation
        error = validate_password(password)
        if error:
            flash(error, 'danger')
            return redirect(url_for('register'))

        if not username or not password:
            flash('Please fill in all fields.', 'warning')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return f"""
            <script>
                alert('Account created successfully! Redirecting to login...');
                window.location.href = '{url_for("login")}';
            </script>
        """

    return render_template('login_base.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))

        flash('Invalid username or password.', 'danger')
    return render_template('login_base1.html')

# Home Page
@app.route('/home')
def home():
    return render_template('base.html', current_user=current_user)

# Index Redirect to Home
@app.route('/')
def index():
    return redirect(url_for('home'))

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

# Protected Page Example
@app.route('/protected')
@login_required
def protected():
    return render_template('protected.html')

# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Store Page
@app.route('/store')
def store():
    return render_template('store.html', current_user=current_user)

@app.route('/logged_users')
@login_required 
def logged_users():
    users = User.query.all() 
    return render_template('logged_users.html', users=users)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html', current_user=current_user)

# API endpoint for sending email
@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    user_email = data.get('email') 
    user_name = data.get('name')  
    user_message = data.get('message') 
    
    if not user_email or not user_name or not user_message:
        return jsonify({'status': 'error', 'message': 'Missing name, email, or message'}), 400
    
    try:
        user_msg = Message(
            subject='Thank You for Contacting Us!',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email],
            body=f"Hello {user_name},\n\nThank you for reaching out. We will get back to you soon!\n\nBest Regards,\nDPP - Dynamic Price Positioning"
        )
        mail.send(user_msg)
        
        admin_msg = Message(
            subject=f'New Contact from {user_name}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_USERNAME']],  
            body=f"Name: {user_name}\nEmail: {user_email}\n\nMessage:\n{user_message}"
        )
        mail.send(admin_msg)
        
        return jsonify({'status': 'success', 'message': 'Email sent successfully'})
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})
    
def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

#$env:MAIL_USERNAME="athithya05amrita@gmail.com"
#$env:MAIL_PASSWORD="itsk yvhv lxlc opaj"
#$env:MAIL_DEFAULT_SENDER="athithya05amrita@gmail.com"