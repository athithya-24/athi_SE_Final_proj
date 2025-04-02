import sqlite3
import secrets
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 📧 Configure Flask-Mail (Set these in the terminal before running)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Set in terminal
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Set in terminal
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# 🛠 Initialize Database
def init_db():
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          name TEXT NOT NULL,
                          email TEXT UNIQUE NOT NULL, 
                          password TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS reset_tokens (
                          email TEXT PRIMARY KEY, 
                          token TEXT)''')
        conn.commit()

init_db()

# 🛠 Function to Get User from Database
def get_user(email):
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, password FROM users WHERE email = ?", (email,))
        return cursor.fetchone()

# 🛠 Function to Add New User
def add_user(name, email, password):
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()

# 🛠 Function to Update User Password
def update_password(email, new_password):
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()

# 🛠 Function to Store Reset Token
def store_reset_token(email, token):
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO reset_tokens (email, token) VALUES (?, ?)", (email, token))
        conn.commit()

# 🛠 Function to Get Reset Token
def get_reset_token(email):
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM reset_tokens WHERE email = ?", (email,))
        return cursor.fetchone()

# 🛠 Function to Delete Reset Token
def delete_reset_token(email):
    with sqlite3.connect("forgot_pass.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reset_tokens WHERE email = ?", (email,))
        conn.commit()

# 🚀 Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if get_user(email):
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        add_user(name, email, password)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login_page'))

    return render_template('fg_register.html')

# 🚀 Login Page
@app.route('/')
def login_page():
    return render_template('fg_login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = get_user(email)
    if user and user[1] == password:
        session['user'] = email
        flash("Login successful!", "success")
        return redirect(url_for('dashboard'))
    
    flash("Invalid credentials!", "danger")
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return f"Welcome, {session['user']}! <a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login_page'))

# 🚀 Forgot Password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if not get_user(email):
            flash("Email not found!", "danger")
            return redirect(url_for('forgot_password'))

        reset_token = secrets.token_urlsafe(16)
        store_reset_token(email, reset_token)
        reset_link = url_for('reset_password', email=email, token=reset_token, _external=True)

        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Click the link to reset your password: {reset_link}"
        mail.send(msg)

        flash("Password reset link sent to your email.", "info")
        return redirect(url_for('login_page'))

    return render_template('fg_forgot.html')

# 🚀 Reset Password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    token = request.args.get('token')

    if request.method == 'POST':
        email = request.form.get('email')
        token = request.form.get('token')
        new_password = request.form.get('new_password')

        stored_token = get_reset_token(email)
        if not stored_token or stored_token[0] != token:
            flash("Invalid or expired token!", "danger")
            return redirect(url_for('login_page'))

        update_password(email, new_password)
        delete_reset_token(email)

        flash("Password has been reset successfully.", "success")
        return redirect(url_for('login_page'))

    if not get_reset_token(email) or get_reset_token(email)[0] != token:
        flash("Invalid or expired token!", "danger")
        return redirect(url_for('login_page'))

    return render_template('fg_reset.html', email=email, token=token)

if __name__ == '__main__':
    app.run(debug=True)


export MAIL_USERNAME="athithya05amrita@gmail.com"
export MAIL_PASSWORD="itsk yvhv lxlc opaj"

export MAIL_DEFAULT_SENDER="athithya05amrita@gmail.com"