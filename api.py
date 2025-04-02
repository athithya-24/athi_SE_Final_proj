from flask import Flask, request, jsonify, render_template
import os
import base64
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# ✅ Initialize Flask App
app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

# ✅ Route for Home Page
@app.route("/")
def home():
    return render_template("forgotpass.html")  # Ensure "forgotpass.html" is in the "templates/" folder

# ✅ User Signup Route
@app.route("/signup", methods=["POST"])
def signup():
    data = request.form
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    return jsonify({"message": f"User {name} signed up successfully!", "email": email})

# ✅ User Login Route
@app.route("/login", methods=["POST"])
def login():
    data = request.form
    email = data.get("email")
    password = data.get("password")

    if email and password:
        return jsonify({"message": "Login successful!"})
    return jsonify({"error": "Invalid credentials"}), 401

# ✅ Forgot Password Route (Accepts User Email)
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    user_email = request.form.get("email")  # Get email from form input
    if not user_email:
        return jsonify({"error": "Email is required"}), 400

    reset_link = f"http://127.0.0.1:5000/reset-password?email={user_email}"

    message = MIMEText(f"Click the following link to reset your password: {reset_link}")
    message["to"] = user_email
    message["subject"] = "Forgot Password - Reset Link"

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service = get_gmail_service()

    try:
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
        return jsonify({"message": f"Forgot password email sent to {user_email}!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Reset Password Page
@app.route("/reset-password")
def reset_password():
    return "Reset your password here"

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
