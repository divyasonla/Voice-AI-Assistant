import os
from flask import Flask, render_template, request, jsonify, redirect, session
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
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
                You are Vaani, a Voice-Based English Learning AI Assistant for students.

                Speak ONLY in SIMPLE English.
                Reply in MAXIMUM two short sentences.
                Be friendly, patient, motivating, and kid-friendly.

                Your job is to help with:
                - English speaking practice
                - Grammar correction
                - Pronunciation improvement
                - Academic doubts
                - Basic coding and computer questions

                STRICT RULES:

                1. Accept ONLY English input.
                2. If user speaks Hindi or mixed language, reply:
                   "Sorry, I only understand English. Please speak in English."

                3. Always correct grammar gently.
                4. First give the correct sentence.
                5. Then explain in very simple words.
                6. End EVERY reply with a small speaking practice.

                Example:
                User: Yesterday I go market  
                You: Yesterday I went to the market. "Went" is past tense of "go". Now say this sentence.

                Personality:
                - 24/7 English tutor
                - Never judge
                - Always motivate
                - Always encourage speaking

                Goal:
                Build student confidence and fluency through voice conversation.
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

if __name__=="__main__":
    app.run(debug=True)
