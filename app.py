from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import os
from datetime import datetime
from database import init_db
from models import (
    login_user, register_user, save_processed_file,
    get_user_history, get_all_users, get_all_history, get_user
)
from detection import (
    process_image, process_video,
    start_webcam, stop_webcam, get_webcam_frame, get_detected_plates
)

app = Flask(__name__)
app.secret_key = "4EF246C33859B457DF9CA73CD2626"
init_db()

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Login ---
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = login_user(username, password)
        if user:
            session["username"] = username
            session["role"] = user[1]
            return redirect(url_for("image_upload"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# --- Register ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if register_user(username, password):
            return redirect(url_for("login"))
        return render_template("register.html", error="Username already exists")
    return render_template("register.html")

# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Image Upload ---
@app.route("/image", methods=["GET", "POST"])
def image_upload():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "image" not in request.files or request.files["image"].filename == "":
            return render_template("image_upload.html", error="Please upload an image")

        file = request.files["image"]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_path = os.path.join(OUTPUT_FOLDER, "processed_" + file.filename)
        file.save(input_path)

        plates = process_image(input_path, output_path)
        save_processed_file(session["username"], "image", input_path, output_path, plates)

        return render_template("image_upload.html", output_file=output_path, plates=plates)

    return render_template("image_upload.html")

# --- Video Upload ---
@app.route("/video", methods=["GET", "POST"])
def video_upload():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "video" not in request.files or request.files["video"].filename == "":
            return render_template("video_upload.html", error="Please upload a video")

        file = request.files["video"]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_path = os.path.join(OUTPUT_FOLDER, "processed_" + file.filename)
        file.save(input_path)

        plates = process_video(input_path, output_path)
        save_processed_file(session["username"], "video", input_path, output_path, plates)

        return render_template("video_upload.html", output_file=output_path, plates=plates)

    return render_template("video_upload.html")

# --- Webcam ---
@app.route("/webcam")
def webcam():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("webcam.html")

@app.route("/start_webcam")
def start_webcam_route():
    start_webcam()
    return redirect(url_for("webcam"))

@app.route("/stop_webcam")
def stop_webcam_route():
    stop_webcam()
    return redirect(url_for("webcam"))

@app.route("/live_feed")
def live_feed():
    frame_path = get_webcam_frame()
    if frame_path:
        return Response(open(frame_path, "rb"), mimetype="image/jpeg")
    return "No feed", 404

@app.route("/get_plates")
def get_plates():
    return jsonify(get_detected_plates())

# --- History ---
@app.route("/history")
def history():
    if "username" not in session:
        return redirect(url_for("login"))
    data = get_user_history(session["username"])
    return render_template("history.html", history=data)

# --- Profile ---
@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    user = get_user(session["username"])
    data = get_user_history(session["username"])
    return render_template("profile.html", user=user, history=data)

# --- Admin Dashboard ---
@app.route("/admin_dashboard")
def admin_dashboard():
    if "username" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    users = get_all_users()
    history = get_all_history()
    return render_template("admin_dashboard.html", users=users, history=history)
