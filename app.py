from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import pickle
import pdfplumber
from model import predict_fraud   # 🔥 ML integration

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- LOAD SMS ML ----------
model = pickle.load(open("sms_model.pkl","rb"))
vectorizer = pickle.load(open("vectorizer.pkl","rb"))

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]

            # OTP generate
            session["otp"] = str(random.randint(1000,9999))

            return redirect("/verify")

        return "Invalid Login ❌"

    return render_template("login.html")

# ---------- OTP VERIFY ----------
@app.route("/verify", methods=["GET","POST"])
def verify():
    if request.method == "POST":
        user_otp = request.form["otp"]

        if user_otp == session.get("otp"):
            return redirect("/sms")
        else:
            return render_template("verify.html", error="Wrong OTP ❌", otp=session.get("otp"))

    return render_template("verify.html", otp=session.get("otp"))

# ---------- SMS ML ----------
@app.route("/sms", methods=["GET","POST"])
def sms():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        sms_text = request.form["sms"]

        vec = vectorizer.transform([sms_text])
        pred = model.predict(vec)[0]
        prob = model.predict_proba(vec)[0][1]

        if pred == 1:
            result = "🚨 Suspicious SMS"
        else:
            result = "✅ Normal SMS"

        confidence = f"{round(prob*100,2)}%"

        return render_template("sms.html", result=result, confidence=confidence)

    return render_template("sms.html")

# ---------- UPLOAD PDF (🔥 ML ADDED HERE) ----------
@app.route("/upload", methods=["GET","POST"])
def upload():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        file = request.files["file"]

        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        transactions = text.split("\n")

        conn = sqlite3.connect("app.db")
        c = conn.cursor()

        fraud = 0
        normal = 0

        for t in transactions:

            # 🔍 amount extract
            try:
                amount = float(''.join([ch for ch in t if ch.isdigit()]))
            except:
                amount = 0

            # 🔥 ML CALL
            data = {"Amount": amount}
            status = predict_fraud(data)

            if status == "Fraud":
                fraud += 1
            else:
                normal += 1

            c.execute(
                "INSERT INTO transactions (user_id,status) VALUES (?,?)",
                (session["user_id"], status)
            )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("upload.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("app.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM transactions WHERE user_id=?", (session["user_id"],))
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM transactions WHERE user_id=? AND status='Fraud'", (session["user_id"],))
    fraud = c.fetchone()[0]

    normal = total - fraud

    conn.close()

    return render_template("dashboard.html", total=total, fraud=fraud, normal=normal)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)