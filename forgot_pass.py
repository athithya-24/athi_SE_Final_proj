from flask import Flask, request, jsonify, session, render_template
from flask_mail import Mail, Message
import random, time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Mail Configuration (Example with Gmail SMTP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your_admin_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Route to serve HTML
@app.route('/')
def index():
    return render_template('a.html')

# 1. Request OTP - Email sent to admin
@app.route('/request_otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    user_email = data.get('email')
    
    # Save user_email in session
    session['user_email'] = user_email

    # Notify admin
    msg = Message('Password Reset Request',
                  sender='your_admin_email@gmail.com',
                  recipients=['admin_recipient_email@example.com'])
    msg.body = f"User {user_email} has requested a password reset. Please generate OTP and send it to the user."
    mail.send(msg)

    return jsonify({'status': 'success', 'message': 'Request sent to admin. Wait for OTP.'})

# 2. Verify OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    user_otp = data.get('otp')
    stored_otp = session.get('otp')
    otp_time = session.get('otp_time')

    if not stored_otp or not otp_time:
        return jsonify({'status': 'failed', 'message': 'No OTP generated.'})

    # Check if OTP is within 4 minutes
    if time.time() - otp_time > 240:
        return jsonify({'status': 'failed', 'message': 'OTP expired. Request again.'})

    if str(user_otp) == str(stored_otp):
        return jsonify({'status': 'verified', 'message': 'OTP verified. Enter new password.'})
    else:
        return jsonify({'status': 'failed', 'message': 'Invalid OTP.'})

# 3. Reset Password
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    new_password = data.get('password')
    user_email = session.get('user_email')

    # Here you should update the password in your database
    print(f"Reset password for {user_email} to {new_password}")

    return jsonify({'status': 'success', 'message': 'Password reset successful.'})

# 4. Admin Route to Generate OTP
@app.route('/generate_otp', methods=['POST'])
def generate_otp():
    data = request.get_json()
    user_email = data.get('email')
    otp = random.randint(100000, 999999)

    # Save OTP and timestamp in session
    session['otp'] = otp
    session['otp_time'] = time.time()

    # Send OTP to user
    msg = Message('Your OTP for Password Reset',
                  sender='your_admin_email@gmail.com',
                  recipients=[user_email])
    msg.body = f"Your OTP is: {otp}. It is valid for 4 minutes."
    mail.send(msg)

    return jsonify({'status': 'success', 'message': f'OTP {otp} sent to {user_email}.'})

if __name__ == '__main__':
    app.run(debug=True)
