from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Replace with your email
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Replace wh your email password  (itsk yvhv lxlc opaj)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')  # Replace with your email

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Create the serializer for tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Create the database and tables
with app.app_context():
    db.create_all()

# Helper Functions
def generate_reset_token(email):
    # Generate a secure token with the user's email
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    # Verify the token and return the email if valid
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', username=user.username)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('register.html')
        
        if existing_email:
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token using itsdangerous
            token = generate_reset_token(user.email)
            
            # Send email
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(
                subject='Password Reset Request',
                recipients=[user.email],
                body=f'Hi {user.username},\n\nTo reset your password, please visit the following link:\n\n{reset_url}\n\nThis link will expire in 1 hour.\n\nIf you did not request a password reset, please ignore this email.'
            )
            
            try:
                mail.send(msg)
                flash('Password reset instructions sent to your email.', 'info')
            except Exception as e:
                flash('Could not send email. Please try again later.', 'danger')
                app.logger.error(f"Email error: {e}")
        else:
            # Don't reveal if email exists in database for security
            flash('If that email is registered, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Verify token and get user email using itsdangerous
    email = verify_reset_token(token)
    
    if email is None:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(debug=True)