import os
from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message

app = Flask(__name__)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Get from environment variable
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Get from environment variable
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER') or app.config['MAIL_USERNAME']

# Print to check if environment variables are being read correctly
print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
print("MAIL_DEFAULT_SENDER:", app.config['MAIL_DEFAULT_SENDER'])

mail = Mail(app)

@app.route('/')
def index():
    return render_template('contact1.html')  # Make sure this matches your HTML file

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    user_email = data.get('email')  # User input email
    user_name = data.get('name')  # User input name
    user_message = data.get('message')  # User input message
    
    if not user_email or not user_name or not user_message:
        return jsonify({'status': 'error', 'message': 'Missing name, email, or message'}), 400
    
    try:
        # Email to the user (confirmation)
        user_msg = Message(
            subject='Thank You for Contacting Us!',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email],
            body=f"Hello {user_name},\n\nThank you for reaching out. We will get back to you soon!\n\nBest Regards,\nAthi"
        )
        mail.send(user_msg)
        
        # Email to you with the user's message
        admin_msg = Message(
            subject=f'New Contact from {user_name}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_USERNAME']],  # Send to your email
            body=f"Name: {user_name}\nEmail: {user_email}\n\nMessage:\n{user_message}"
        )
        mail.send(admin_msg)
        
        return jsonify({'status': 'success', 'message': 'Email sent successfully'})
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

 export MAIL_USERNAME="athithya05amrita@gmail.com"
 export MAIL_PASSWORD="itskyvhvlxlcopaj"
 export MAIL_DEFAULT_SENDER="athithya05amrita@gmail.com"