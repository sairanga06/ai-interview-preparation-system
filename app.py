import re
import random
import sqlite3
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import google.generativeai as genai
from dotenv import load_dotenv
from groq import Groq
from abc import ABC, abstractmethod

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "interview_project_secret_2026"
load_dotenv()

print("Current Directory:", os.getcwd())


groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=60.0,
    max_retries=2
)

class ChatBase(ABC):
    @abstractmethod
    def complete_prompt(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def evaluate_answer(self, question: str, answer: str) -> tuple[float, str]:
        raise NotImplementedError

class chat(ChatBase):
    def __init__(self, client=None, model="llama-3.3-70b-versatile"):
        self.client = client if client is not None else groq_client
        self.model = model

    def complete_prompt(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def evaluate_answer(self, question: str, answer: str) -> tuple[float, str]:
        prompt = f"""
You are a Senior Technical Interviewer.

Evaluate the following interview answer professionally.

Question:
{question}

Candidate Answer:
{answer}

Return ONLY in the following format:

⭐ Score: X/10

💬 Feedback
Explain in 3-5 sentences.

✅ Strengths
• Point 1
• Point 2

🚀 Improvements
• Point 1
• Point 2
• Point 3

📚 Recommended Answer
Provide the ideal interview answer in 3-5 sentences.

Keep the response professional and concise.
"""
        content = self.complete_prompt(prompt)
        score_match = re.search(r"([0-9]+(?:\.[0-9]+)?)/10", content)

        if not score_match:
            score_match = re.search(r"Score:\s*([0-9]+(?:\.[0-9]+)?)", content)

        score = float(score_match.group(1)) if score_match else 5.0
        return score, content

@app.route("/test_groq")
def test_groq():

    try:

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": "Say Hello from Groq!"
                }
            ]

        )

        return response.choices[0].message.content

    except Exception as e:

        return str(e)

# ==========================
# Test Grok AI
# ==========================


# ==========================
# Gemini Configuration
# ==========================

model = genai.GenerativeModel("gemini-2.0-flash")

# ==========================
# Interview Questions
# ==========================
question_bank = {

    "python": {

        "easy": [
            "What is Python?",
            "What is a Variable?",
            "What is a List?",
            "What is a Tuple?",
            "What is a Dictionary?"
        ],

        "medium": [
            "Difference between List and Tuple?",
            "Explain Lambda Functions.",
            "Explain Exception Handling.",
            "What are Modules?",
            "Explain File Handling."
        ],

        "hard": [
            "Explain Decorators.",
            "What is GIL?",
            "What are Generators?",
            "Explain Iterators.",
            "Explain Memory Management."
        ]
    },

    "sql": {

        "easy": [
            "What is SQL?",
            "What is a Database?",
            "What is a Table?",
            "What is a Row?",
            "What is a Column?"
        ],

        "medium": [
            "What is Primary Key?",
            "Difference between WHERE and HAVING?",
            "Explain JOIN.",
            "What is GROUP BY?",
            "What is ORDER BY?"
        ],

        "hard": [
            "Explain Normalization.",
            "Difference between DELETE and TRUNCATE.",
            "What are Indexes?",
            "Explain Transactions.",
            "What are Views?"
        ]
    },
    
    "django": {

    "easy": [
        "What is Django?",
        "What is Django used for?",
        "What is a Django Project?",
        "What is a Django App?",
        "How do you create a Django project?"
    ],

    "medium": [
        "What is MTV architecture?",
        "Explain Django ORM.",
        "What are Django Models?",
        "What are Django Views?",
        "What are Django Templates?"
    ],

    "hard": [
        "Explain Django Middleware.",
        "What are Class-Based Views?",
        "What is Django REST Framework?",
        "How does Authentication work in Django?",
        "Explain Django Signals."
    ]
    },
    "flask": {

    "easy": [
        "What is Flask?",
        "What is Flask used for?",
        "How do you create a Flask app?",
        "What is app.py?",
        "How do you run a Flask application?"
    ],

    "medium": [
        "Explain Flask Routing.",
        "What are Templates in Flask?",
        "Explain Jinja2.",
        "What is request in Flask?",
        "What is render_template()?"
    ],

    "hard": [
        "Explain Flask Sessions.",
        "How does Flask connect to databases?",
        "Explain Blueprints.",
        "How do you deploy a Flask app?",
        "Explain Flask REST APIs."
    ]
    },
    "html": {

    "easy": [
        "What is HTML?",
        "What is CSS?",
        "What is a Tag?",
        "What is an Attribute?",
        "Difference between HTML and CSS?"
    ],

    "medium": [
        "Explain Flexbox.",
        "Explain CSS Grid.",
        "Difference between id and class.",
        "What are Semantic Tags?",
        "Explain Forms in HTML."
    ],

    "hard": [
        "What is Responsive Design?",
        "Explain Media Queries.",
        "Difference between inline, block and inline-block.",
        "Explain CSS Position properties.",
        "What is the Box Model?"
    ]
    },
    "javascript": {

    "easy": [
        "What is JavaScript?",
        "What are Variables?",
        "Difference between let, var and const.",
        "What is a Function?",
        "What is an Array?"
    ],

    "medium": [
        "Explain DOM.",
        "What are Events?",
        "Explain Arrow Functions.",
        "What are Objects?",
        "Difference between == and ===."
    ],

    "hard": [
        "Explain Promises.",
        "Explain Async/Await.",
        "What is Event Bubbling?",
        "Explain Closures.",
        "What is Hoisting?"
    ]
    },
    "oop": {

    "easy": [
        "What is Object Oriented Programming?",
        "What is a Class?",
        "What is an Object?",
        "What is a Method?",
        "What is an Attribute?"
    ],

    "medium": [
        "Explain Encapsulation.",
        "Explain Inheritance.",
        "Explain Polymorphism.",
        "Explain Abstraction.",
        "Difference between Class and Object."
    ],

    "hard": [
        "Explain Method Overriding.",
        "Explain Method Overloading.",
        "What is Multiple Inheritance?",
        "Explain Constructor and Destructor.",
        "Explain MRO in Python."
    ]
    },
    "dsa": {

    "easy": [
        "What is Data Structure?",
        "What is an Algorithm?",
        "What is an Array?",
        "What is a Linked List?",
        "What is a Stack?"
    ],

    "medium": [
        "What is a Queue?",
        "Explain Binary Search.",
        "Explain Linear Search.",
        "What is Time Complexity?",
        "Difference between Stack and Queue."
    ],

    "hard": [
        "Explain Trees.",
        "Explain Graphs.",
        "Explain Hash Tables.",
        "What is Dynamic Programming?",
        "Explain Recursion."
    ]
}
}





current_question = 0
answers = []
scores = []
feedbacks = []

# ==========================
# Create Database
# ==========================
def create_database():
    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT,
        answer TEXT,
        score INTEGER,
        feedback TEXT,
        interview_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
    cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

    cursor.execute("""
    INSERT OR IGNORE INTO admins(username, email, password)
    VALUES(
    'Administrator',
    'admin@gmail.com',
    'admin123'
)
""")

    conn.commit()
    conn.close()

create_database()

# ==========================
# Home Page
# ==========================
@app.route("/")
def home():
    global current_question, answers, scores, feedbacks

    current_question = 0
    answers = []
    scores = []
    feedbacks = []
    session.pop("category", None)
    session.pop("difficulty", None)
    session.pop("questions", None)
    

    return render_template("index.html")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users(username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, hashed_password))

        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

      
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute("""
             SELECT * FROM users
             WHERE email=?
        """, (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect(url_for("dashboard"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    # Total interview records
    cursor.execute("""
        SELECT COUNT(*)
        FROM interviews
        WHERE user_id = ?
    """, (session["user_id"],))

    total_interviews = cursor.fetchone()[0]
    

    # Average score
    cursor.execute("""
        SELECT AVG(score)
        FROM interviews
        WHERE user_id = ?
    """, (session["user_id"],))

    avg_score = cursor.fetchone()[0]

    if avg_score is None:
        avg_score = 0
    else:
        avg_score = round(avg_score, 2)

    # Best score
    cursor.execute("""
        SELECT MAX(score)
        FROM interviews
        WHERE user_id = ?
    """, (session["user_id"],))
    best_score = cursor.fetchone()[0]

    # Recent scores (ordered oldest -> newest)
    cursor.execute("""
    SELECT score
    FROM interviews
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT 10
    """, (session["user_id"],))

    scores = [row[0] for row in cursor.fetchall()]

    scores.reverse()

    print("Number of scores:", len(scores))
    print("Scores:", scores)
    # ==========================
    # Recent Interviews
    # ==========================

    cursor.execute("""
        SELECT interview_date, question, score
        FROM interviews
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (session["user_id"],))

    recent_interviews = cursor.fetchall()

    conn.close()
    return render_template(
        "dashboard.html",
        username=session["username"],
        total_interviews=total_interviews,
        avg_score=avg_score,
        best_score=best_score,
        scores=scores,
        recent_interviews=recent_interviews
    )
@app.route("/category")
def category():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("category.html")
@app.route("/set_category", methods=["POST"])
def set_category():

    if "user_id" not in session:
        return redirect(url_for("login"))

    session["category"] = request.form["category"]
    session["difficulty"] = request.form["difficulty"]

    current_category = session["category"]
    current_difficulty = session["difficulty"]

    all_questions = question_bank[current_category][current_difficulty]

    session["questions"] = random.sample(
        all_questions,
        min(5, len(all_questions))
    )

    return redirect(url_for("interview"))
@app.route("/interview")
def interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if "questions" not in session:
        return redirect(url_for("category"))

    global current_question

    questions = session["questions"]

    return render_template(
        "interview.html",
        question=questions[current_question],
        number=current_question + 1,
        total=len(questions),
        category=session["category"].title(),
        difficulty=session["difficulty"].title()
    )
@app.route("/submit", methods=["POST"])
def submit():

    global current_question, answers, scores, feedbacks

    if "user_id" not in session:
        return redirect(url_for("login"))

    questions = session["questions"]

    answer = request.form["answer"]

    answers.append(answer)

    current_question += 1

    # Show next question
    if current_question < len(questions):

        return render_template(
            "interview.html",
            question=questions[current_question],
            number=current_question + 1,
            total=len(questions),
            category=session["category"].title(),
            difficulty=session["difficulty"].title()
        )

    # ==========================
    # Interview Completed
    # ==========================

    scores.clear()
    feedbacks.clear()

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()
    evaluator = chat()

    for i in range(len(answers)):
        answer = answers[i]
        try:
            score, feedback = evaluator.evaluate_answer(questions[i], answer)
        except Exception as e:
          print("========== GROQ AI ERROR ==========")
          print(repr(e))
          print("====================================")

          score = 5
          feedback = f"AI Evaluation Error: {str(e)}"
        scores.append(score)
        feedbacks.append(feedback)
        cursor.execute("""
            INSERT INTO interviews
            (user_id, question, answer, score, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            questions[i],
            answer,
            score,
            feedback
        ))
    conn.commit()
    conn.close()
    return render_template(
        "summary.html",
        questions=questions,
        answers=answers,
        scores=scores,
        feedbacks=feedbacks
    )
    # Show next question
   
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT question, answer, score, feedback, interview_date
        FROM interviews
        WHERE user_id = ?
        ORDER BY interview_date DESC
    """, (session["user_id"],))

    history = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history
    )

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    # ==========================
    # Total Users
    # ==========================
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # ==========================
    # Total Interview Records
    # ==========================
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]

    # ==========================
    # Average Score
    # ==========================
    cursor.execute("SELECT AVG(score) FROM interviews")
    avg_score = cursor.fetchone()[0]

    if avg_score is None:
        avg_score = 0
    else:
        avg_score = round(avg_score, 2)

    # ==========================
    # Highest Score
    # ==========================
    cursor.execute("SELECT MAX(score) FROM interviews")
    highest_score = cursor.fetchone()[0]

    if highest_score is None:
        highest_score = 0

    # ==========================
    # Recent Interviews
    # ==========================
    cursor.execute("""
        SELECT interview_date, question, score
        FROM interviews
        ORDER BY interview_date DESC
        LIMIT 5
    """)
    recent_interviews = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        username=session.get("admin"),
        total_users=total_users,
        total_interviews=total_interviews,
        avg_score=avg_score,
        highest_score=highest_score,
        recent_interviews=recent_interviews
    )
@app.route("/admin/users")
def admin_users():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "")

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    if search:

        cursor.execute("""
            SELECT id, username, email
            FROM users
            WHERE username LIKE ?
               OR email LIKE ?
        """, ('%' + search + '%', '%' + search + '%'))

    else:

        cursor.execute("""
            SELECT id, username, email
            FROM users
        """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users,
        search=search
    )

@app.route("/admin/interviews")
def admin_interviews():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "")

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    if search:

        cursor.execute("""
        SELECT
            interviews.id,
            users.username,
            interviews.question,
            interviews.answer,
            interviews.score,
            interviews.feedback,
            interviews.interview_date
        FROM interviews
        JOIN users
        ON interviews.user_id = users.id
        WHERE users.username LIKE ?
           OR interviews.question LIKE ?
           OR interviews.answer LIKE ?
           OR interviews.interview_date LIKE ?
        ORDER BY interviews.interview_date DESC
        """, (
            '%' + search + '%',
            '%' + search + '%',
            '%' + search + '%',
            '%' + search + '%'
        ))

    else:

        cursor.execute("""
        SELECT
            interviews.id,
            users.username,
            interviews.question,
            interviews.answer,
            interviews.score,
            interviews.feedback,
            interviews.interview_date
        FROM interviews
        JOIN users
        ON interviews.user_id = users.id
        ORDER BY interviews.interview_date DESC
        """)

    interviews = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_interviews.html",
        interviews=interviews,
        search=search
    )
@app.route("/admin/delete_interview/<int:interview_id>")
def delete_interview(interview_id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM interviews
    WHERE id = ?
    """, (interview_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_interviews"))
# ==========================
# Admin Login
# ==========================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM admins
        WHERE email=? AND password=?
        """, (email, password))

        admin = cursor.fetchone()

        conn.close()

        if admin:

            session["admin"] = admin[1]

            return redirect(url_for("admin_dashboard"))

        else:

            return "Invalid Admin Login"

    return render_template("admin_login.html")
@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    # Delete all interview records of the user
    cursor.execute("""
    DELETE FROM interviews
    WHERE user_id = ?
    """, (user_id,))

    # Delete the user
    cursor.execute("""
    DELETE FROM users
    WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_users"))
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        cursor.execute("""
            UPDATE users
            SET username=?, email=?
            WHERE id=?
        """, (username, email, session["user_id"]))

        conn.commit()

        session["username"] = username

        conn.close()

        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT username, email
        FROM users
        WHERE id=?
    """, (session["user_id"],))

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )
@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT password
            FROM users
            WHERE id=?
        """, (session["user_id"],))

        db_password = cursor.fetchone()[0]

        if not check_password_hash(db_password, current_password):

           conn.close()
           return "Current Password is Incorrect!"

        if new_password != confirm_password:

            conn.close()
            return "New Passwords do not match!"

        hashed_new_password = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE users
            SET password=?
            WHERE id=?
        """, (hashed_new_password, session["user_id"]))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("change_password.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/download_certificate")
def download_certificate():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(score)
        FROM interviews
        WHERE user_id = ?
    """, (session["user_id"],))

    best_score = cursor.fetchone()[0]
    conn.close()

    if best_score is None:
        best_score = 0

    filename = "static/certificate.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    width, height = letter

    # ==========================
    # Border
    # ==========================
    c.setStrokeColorRGB(0.25, 0.20, 0.80)
    c.setLineWidth(4)
    c.rect(30, 30, width - 60, height - 60)

    # ==========================
    # Certificate Title
    # ==========================
    c.setFillColorRGB(0.78, 0.60, 0.10)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, 740, "CERTIFICATE OF COMPLETION")

    # Back to Black
    c.setFillColorRGB(0, 0, 0)

    # ==========================
    # Project Name
    # ==========================
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, 700, "AI Interview Preparation System")

    # ==========================
    # Presented To
    # ==========================
    c.setFont("Helvetica", 16)
    c.drawCentredString(
        width / 2,
        640,
        "This Certificate is Proudly Presented To"
    )

    # ==========================
    # Username (Blue)
    # ==========================
    c.setFillColorRGB(0.20, 0.30, 0.90)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, 590, session["username"])

    # Back to Black
    c.setFillColorRGB(0, 0, 0)

    # ==========================
    # Description
    # ==========================
    c.setFont("Helvetica", 16)
    c.drawCentredString(
        width / 2,
        540,
        "For Successfully Completing the AI Mock Interview"
    )

    # ==========================
    # Best Score (Red)
    # ==========================
    c.setFillColorRGB(0.85, 0.10, 0.10)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(
        width / 2,
        490,
        f"Best Score : {best_score}/10"
    )

    # Back to Black
    c.setFillColorRGB(0, 0, 0)

    # ==========================
    # Date
    # ==========================
    c.setFont("Helvetica", 16)
    c.drawCentredString(
        width / 2,
        455,
        f"Date : {__import__('datetime').datetime.now().strftime('%d-%m-%Y')}"
    )

    # ==========================
    # Signature Lines
    # ==========================
    c.line(80, 120, 220, 120)
    c.line(390, 120, 530, 120)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 100, "AI Interview Prep")
    c.drawString(420, 100, "Authorized Sign")

    c.save()

    return redirect(url_for("static", filename="certificate.pdf"))

if __name__ == "__main__":
    app.run(debug=True)