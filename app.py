import os
from flask import Flask, render_template, request, jsonify, redirect, session
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

# Replace hardcoded API key with environment variable
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("API_KEY")
)

# fake DB
users = {}
history = {}

# ================= HOME =================

@app.route("/")
def home():
    if "user" in session:
        return redirect("/chat")
    return render_template("login.html")

# ================= SIGNUP =================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # empty check
        if not username or not password or not confirm_password:
            return "All fields are required!", 400

        # password match
        if password != confirm_password:
            return "Passwords do not match!"

        # existing user
        if username in users:
            return "User already exists! Please log in."

        # save user
        users[username] = {
            'username': username,
            'password': generate_password_hash(password)
        }

        # Log the user in by setting session
        session['user'] = username
        return redirect('/chat')

    return render_template('signup.html')

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Username and password are required!", 400

        user = users.get(username)
        if not user or not check_password_hash(user['password'], password):
            return "Invalid credentials!"

        # Log the user in by setting session
        session['user'] = username
        return redirect('/chat')

    return render_template('login.html')

# ================= CHAT PAGE =================

@app.route("/chat", methods=["GET","POST"])
def chat():

    if 'user' not in session or session['user'] is None:
        return redirect('/login')

    username = session['user']

    # Initialize history for the user if it doesn't exist
    if username not in history:
        history[username] = []
    if request.method == "GET":
        return render_template("index.html")

    user_input = request.json.get("message")

    if not user_input:
        return jsonify({"response": "Say something!"})

    completion = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {
                "role": "system",
                "content": """
                    You are a Voice-Based English Learning AI Assistant designed for students.

                    IMPORTANT RULES:
                    
                    1. You ONLY understand and respond in ENGLISH.
                    2. If the user speaks Hindi or any other language, politely reply:
                       "Please speak in English. I only understand English."
                    
                    3. Users are NOT allowed to type. They communicate only through voice.
                    
                    4. Your main goals:
                       - Help users improve English speaking
                       - Correct grammar and pronunciation
                       - Build confidence in conversation
                       - Solve academic doubts
                       - Teach basic programming and technical concepts
                    
                    5. You behave like a friendly English tutor and coding mentor.
                    
                    6. If the user makes grammar mistakes:
                       - First repeat the correct sentence
                       - Then explain simply.
                    
                    Example:
                    User: "He go to school"
                    AI:
                    "Correct sentence: He goes to school.
                    Explanation: With 'he', we use 'goes'."
                    
                    7. For coding questions:
                       - Explain in very simple English
                       - Give short examples
                       - Act like a beginner-friendly teacher.
                    
                    Supported coding topics:
                    - HTML
                    - CSS
                    - JavaScript
                    - Python
                    - Basic AI concepts
                    - Programming fundamentals
                    
                    8. Always motivate students.
                    
                    9. Keep answers short, clear, and student-friendly.
                    
                    10. You are available 24/7 as an English speaking partner.
                    
                    PERSONALITY:
                    Friendly, patient, encouraging English teacher.
                    
                    MISSION:
                    Help students speak fluent English and learn technology through voice conversation only.

                """
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        temperature=0.6,
        max_tokens=100
    )

    bot = completion.choices[0].message.content

    # Append the conversation to the user's history
    history[username].append({
        "user": user_input,
        "bot": bot
    })

    return jsonify({"response": bot})

# ================= HISTORY =================

@app.route("/history")
def get_history():

    if "user" not in session:
        return jsonify([])

    return jsonify(history[session["user"]])

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
