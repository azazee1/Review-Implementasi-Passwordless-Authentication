from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import smtplib
import qrcode
import uuid
import os
from email.mime.text import MIMEText
import random
import json
import cv2
import numpy as np
import base64

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

REGISTERED_FACE = None  # Embedding wajah tersimpan
stored_face = None

app = Flask(__name__)
app.secret_key = "jcfi wluu yhuy rods"
saved_behavior = {}

# TEMP STORAGE
magic_tokens = {}
otp_codes = {}

# EMAIL CONFIG
EMAIL_ADDRESS = "trsleomecha@gmail.com"
EMAIL_PASSWORD = "jcfi wluu yhuy rods"

login_tokens = {}

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    # untuk demo, login selalu berhasil tanpa username/password
    return redirect(url_for("select_verification"))

@app.route("/select-verification")
def select_verification():
    return render_template("select_verification.html")

@app.route("/qr-login")
def qr_login():
    token = str(uuid.uuid4())
    login_tokens[token] = False

    verify_url = f"http://127.0.0.1:5000/verify/{token}"
    img = qrcode.make(verify_url)
    qr_path = f"static/{token}.png"
    img.save(qr_path)

    return render_template("qrcode_page.html", qr_path=qr_path, token=token)

@app.route("/verify/<token>")
def verify(token):
    if token in login_tokens:
        login_tokens[token] = True
        return redirect("/dashboard")
    return "<h2>Token tidak valid.</h2>"

@app.route("/status/<token>")
def status(token):
    if login_tokens.get(token):
        return "Login Sukses"
    return "Menunggu Verifikasi..."


# MAGIC LINK

@app.route("/magiclink")
def magiclink_page():
    return render_template("magiclink.html")

@app.route("/send_magic", methods=["POST"])
def send_magic():
    user_email = request.form["email"]
    token = str(uuid.uuid4())
    magic_tokens[token] = True

    verify_url = f"http://127.0.0.1:5000/magic_verify/{token}"
    msg = MIMEText(f"Klik Magic Link untuk login:\n{verify_url}")
    msg["Subject"] = "Magic Link Login"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = user_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

    return "<h3>Magic link telah dikirim ke email kamu.</h3>"

@app.route("/magic_verify/<token>")
def magic_verify(token):
    if token in magic_tokens:
        session["logged_in"] = True
        return redirect("/dashboard")
    return "Link tidak valid."


# KODE OTP

@app.route("/otp")
def otp_page():
    return render_template("otp.html")

@app.route("/send_otp", methods=["POST"])
def send_otp():
    email = request.form["email"]
    otp = random.randint(100000, 999999) 
    otp_codes[email] = otp

    msg = MIMEText(f"Kode OTP Anda: {otp}")
    msg["Subject"] = "OTP Login"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

    return render_template("verify_otp.html", email=email)

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form["email"]
    otp = request.form["otp"]

    if email in otp_codes and str(otp_codes[email]) == otp:
        session["logged_in"] = True
        return redirect("/dashboard")

    return "<h3>OTP salah!</h3>"


# BEHAVIORAL AUTHENTICATION

@app.route("/behavioral")
def behavioral_page():
    return render_template("behavioral.html")


@app.route("/register-behavior")
def register_behavior_page():
    return render_template("register_behavior.html")


@app.route("/save-behavior", methods=["POST"])
def save_behavior():
    data = request.get_json()

    # Validasi teks wajib
    if data["typed_text"].strip().lower() != "login verification":
        return jsonify({"status": "error", "message": "Teks tidak sesuai"}), 400

    saved_behavior["speed"] = data["typing_speed"]
    saved_behavior["delay"] = data["average_delay"]

    return jsonify({"status": "ok", "message": "Pola berhasil disimpan"})


@app.route("/verify-behavior", methods=["POST"])
def verify_behavior():
    if not saved_behavior:
        return jsonify({"status": "error", "message": "Belum ada pola tersimpan"})

    data = request.get_json()

    # Validasi teks
    if data["typed_text"].strip().lower() != "login verification":
        return jsonify({"status": "error", "message": "Teks salah"}), 400

    typed_speed = data["typing_speed"]
    typed_delay = data["average_delay"]

    base_speed = saved_behavior["speed"]
    base_delay = saved_behavior["delay"]

    # Perbandingan pola: toleransi 20%
    if abs(typed_speed - base_speed) <= base_speed * 0.2 and \
       abs(typed_delay - base_delay) <= base_delay * 0.2:
        return jsonify({"status": "ok", "message": "Behavior cocok! Login Berhasil"})

    return jsonify({"status": "error", "message": "Pola tidak cocok"})


# FACE RECOGNITION

FACE_DIR = "face_data"
os.makedirs(FACE_DIR, exist_ok=True)

@app.route("/face")
def face_page():
    return render_template("face_menu.html")

@app.route("/face-register", methods=["GET", "POST"])
def face_register():
    global REGISTERED_FACE

    if request.method == "POST":
        file = request.files["image"]
        img_np = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            return "Wajah tidak terdeteksi, coba ulangi."

        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]

        REGISTERED_FACE = cv2.resize(face_roi, (200, 200))

        return "<h3>Wajah berhasil didaftarkan!</h3><a href='/select-verification'>Kembali</a>"

    return render_template("face_register.html")

@app.route("/face-login")
def face_login():
    return render_template("face_login.html")

@app.route("/face-login-stream", methods=["POST"])
def face_login_stream():
    global REGISTERED_FACE

    if REGISTERED_FACE is None:
        return jsonify({"status": "error", "message": "Belum ada wajah terdaftar!"})

    file = request.files["frame"]
    frame = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return jsonify({"status": "no_face"})

    (x, y, w, h) = faces[0]
    face_roi = gray[y:y+h, x:x+w]
    face_roi = cv2.resize(face_roi, (200, 200))

    # Buat score wajah
    diff = cv2.absdiff(REGISTERED_FACE, face_roi)
    score = np.mean(diff)

    if score < 35:  # threshold bisa disesuaikan
        session["logged_in"] = True
        return jsonify({"status": "success"})

    return jsonify({"status": "fail"})


# DASHBOARD

@app.route("/dashboard")
def dashboard():
    if "logged_in" in session:
        return "<h2>Login berhasil! Pilih metode verifikasi lain di sini.</h2>"
    return redirect("/")

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
