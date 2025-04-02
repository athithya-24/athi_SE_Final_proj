from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import os
import re  # For password validation
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key_here_123'

# Database Setup
db_path = os.path.join(os.path.abspath(os.getcwd()), 'user_auth10.db')
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

# Updated User Model with email field
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
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

# Email Validation Function
def validate_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return "Please enter a valid email address."
    return None

# Load and process product data
def load_product_data():
    try:
        # Load Excel data
        df = pd.read_excel("updated_pro_duct.xlsx", dtype={"image": str})
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
        
        return products, predicted_products
    except Exception as e:
        print(f"Error loading product data: {str(e)}")
        return [], []

# Initialize global products variables
products, predicted_products = [], []

# Generate a token for password reset
def get_reset_token(user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='password-reset-salt')

# Verify the token
def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
    except (SignatureExpired, BadTimeSignature):
        return None
    return User.query.get(user_id)

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Email validation
        email_error = validate_email(email)
        if email_error:
            flash(email_error, 'danger')
            return redirect(url_for('register'))

        # Password Validation
        password_error = validate_password(password)
        if password_error:
            flash(password_error, 'danger')
            return redirect(url_for('register'))

        if not name or not email or not password:
            flash('Please fill in all fields.', 'warning')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Send welcome email
        try:
            welcome_msg = Message(
                subject='Welcome to DPP - Dynamic Price Prediction!',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            welcome_msg.body = f"""Hello {name},

Thank you for registering with DPP - Dynamic Price Prediction!

Your account has been successfully created. You can now log in using your email and password.

Best Regards,
The DPP Team
"""
            mail.send(welcome_msg)
        except Exception as e:
            print(f"Error sending welcome email: {str(e)}")

        flash('Account created successfully!', 'success')
        return f"""
            <script>
                alert('Account created successfully! Redirecting to login...');
                window.location.href = '{url_for("login")}';
            </script>
        """

    return render_template('final_register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))

        flash('Invalid email or password.', 'danger')
    return render_template('final_login.html')

# Forgot Password Route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Email validation
        email_error = validate_email(email)
        if email_error:
            flash(email_error, 'danger')
            return redirect(url_for('forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            token = get_reset_token(user.id)
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Email the user
            try:
                msg = Message(
                    'Password Reset Request',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )
                msg.body = f"""Hello {user.name},

To reset your password, visit the following link:
{reset_url}

This link will expire in 1 hour.

If you did not make this request, simply ignore this email and no changes will be made.

Best Regards,
The DPP Team
"""
                mail.send(msg)
                flash('A password reset link has been sent to your email.', 'info')
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                flash('There was an error sending the password reset email. Please try again later.', 'danger')
            
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'danger')
    
    return render_template('final_forgot_password.html')

# Reset Password Route
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    user = verify_reset_token(token)
    
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        
        # Password Validation
        error = validate_password(new_password)
        if error:
            flash(error, 'danger')
            return redirect(url_for('reset_password', token=token))
        
        # Hash and update the password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        
        # Send confirmation email
        try:
            confirm_msg = Message(
                subject='Password Reset Confirmation',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            confirm_msg.body = f"""Hello {user.name},

Your password has been successfully reset.

If you did not make this change, please contact our support team immediately.

Best Regards,
The DPP Team
"""
            mail.send(confirm_msg)
        except Exception as e:
            print(f"Error sending confirmation email: {str(e)}")
        
        flash('Your password has been updated! You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
        
    return render_template('final_reset_password.html', token=token)

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
@login_required
def store():
    return render_template('store.html', current_user=current_user)

@app.route('/aboutus')
@login_required
def aboutus():
    return render_template('aboutus.html', current_user=current_user)
# Original Products Page
@app.route('/original')
def original_products():
    global products, predicted_products
    if not products:
        products, predicted_products = load_product_data()
    return render_template("original.html", products=products, current_user=current_user)

# Predicted Products Page
@app.route('/predicted')
def predicted_products_page():
    global products, predicted_products
    if not products:
        products, predicted_products = load_product_data()
    return render_template("duplicate.html", products=predicted_products, current_user=current_user)

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
            body=f"Hello {user_name},\n\nThank you for reaching out. We will get back to you soon!\n\nBest Regards,\nDPP - Dynamic Price Prediction"
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
    # Load product data at startup
    products, predicted_products = load_product_data()
    app.run(debug=True, host='0.0.0.0', port=5000)


    #$env:MAIL_DEFAULT_SENDER="athithya05amrita@gmail.com"
    #$env:MAIL_USERNAME="athithya05amrita@gmail.com" 
    #$env:MAIL_USERNAME="athithya05amrita@gmail.com" 
    #$env:MAIL_PASSWORD="itsk yvhv lxlc opaj"