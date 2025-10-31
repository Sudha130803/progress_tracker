from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = "supersecretkey"

# Database connection
conn = psycopg2.connect(
    dbname="progress",
    user="postgres",
    password="2003",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# frontend routes

@app.route("/")
def index():
    return render_template("index1.html")


@app.route("/login_page", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

@app.route("/register")
def register():
    return render_template("registration.html")

@app.route('/student_page')
def student_page():
    return render_template("student.html")

@app.route('/bothCourse_page')
def both_page():
    return render_template("bothCourse.html")

@app.route("/dashboard", methods=["GET"])
def student_dashboard():
    if "student_id" not in session:
        return redirect("/")
    cursor.execute("SELECT fullname, email, skills, course FROM students WHERE id=%s", 
                  (session["student_id"],))
    student = cursor.fetchone()
    return render_template("student_dashboard.html", student=student)

@app.route("/admin/register_page", methods=["GET"])
def admin_register_page():
    return render_template("admin_register.html")

@app.route("/admin/login_page", methods=["GET"])
def admin_login_page():
    return render_template("admin_login.html")

@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/admin/login_page")
    cursor.execute("SELECT id, fullname, email, skills, course FROM students")
    students = cursor.fetchall()
    return render_template("admin_dashboard.html", students=students)


# Route for registration
@app.route('/register', methods=["POST"])
def student_register():
    data = request.get_json(silent=True) or {}

    fullname = data.get("fullname") or data.get("name")
    email = data.get("email")
    password = data.get("password")
    skills = data.get("skills")
    course = data.get("course")
    
    if not all([fullname, email, password, skills, course]):
        return jsonify(error="All fields are required."),400
    
    hash_password = generate_password_hash(password)

    try:
        cursor.execute("""
            INSERT INTO students (fullname, email, password, skills, course)
            VALUES (%s, %s, %s, %s, %s)
        """, (fullname, email, hash_password, skills, course))
        conn.commit()
        return jsonify(message="Registration successful!"), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify(error =str(e)),500
    

# student login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    cursor = conn.cursor()
    cursor.execute("SELECT id, fullname, email, password, skills, course FROM students WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Invalid login credentials"}), 401

    if not check_password_hash(user[3], password):
        return jsonify({"error":"Invalid login credentials"}), 401

    session["student_id"] = user[0]

    courses = [c.strip() for c in user[5].split(",")]
    if "Technical" in courses and "Corporate" in courses:
        redirect_url=f"/bothCourse_page?id={user[0]}"
    else:
        redirect_url = f"/student_page?id={user[0]}"
    return jsonify({
        "message":"Login successful",
        "student":{
            "id": user[0],
            "fullname": user[1],
            "email": user[2],
            "skills": user[4],
            "course": user[5]
        },
        "redirect": redirect_url
    })


# Student progress routes

@app.route("/student/<int:student_id>", methods=["GET"])
def get_student(student_id):
    cursor.execute("SELECT id, fullname, email, skills, course FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    cursor.execute("""
        SELECT course_type, completed_modules, last_activity, COALESCE(recent_activity, '{}')
        FROM student_progress WHERE student_id = %s
    """, (student_id,))
    progress_rows = cursor.fetchall()

    progress = {}
    last_activity = None
    recent_activity = None
    for row in progress_rows:
        course_type, completed_modules, last_act, recent_act =row
        course_type = course_type.capitalize()
        progress[course_type]=completed_modules

        if last_act and (last_activity is None or last_act > last_activity):
            last_activity = last_act
        if recent_act and (recent_activity is None or recent_act > recent_activity):
            recent_activity = recent_act

    return jsonify({
        "id": student[0],
        "fullname": student[1],
        "email": student[2],
        "skills": student[3],
        "course": student[4],
        "progress": progress,
        "last_activity": last_activity if last_activity else None,
        "recent_activity": recent_activity if recent_activity else None
    })

@app.route("/student/<int:student_id>/update", methods=["POST"])
def update_student_progress(student_id):
    data = request.get_json()

    course_type = data.get('course_type', "")
    if not course_type:
        return jsonify (error = "Course type is required"), 400
    
    course_type = course_type.capitalize()

    completed_modules = data.get("completed_modules", 0)
    

    try:

        cursor.execute("SELECT completed_modules FROM student_progress WHERE student_id=%s AND course_type=%s", (student_id, course_type))
        row = cursor.fetchone()
        current_completed = row[0] if row else 0

        if  course_type == "Technical":
            max_modules = 15
        elif course_type == "Corporate":
            max_modules = 15
        else:
            max_modules = 0

        new_completed = min(current_completed + completed_modules, max_modules)

        cursor.execute("""
            INSERT INTO student_progress (student_id, course_type, completed_modules, last_activity)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (student_id, course_type) DO UPDATE
            SET completed_modules = %s,
                   last_activity = NOW()
        """, (student_id, course_type, new_completed, new_completed))
        conn.commit()

        return jsonify(message = "Progress uploaded successfully", completed = new_completed), 200

    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 500

@app.route("/student/<int:student_id>/reset", methods=["POST"])
def reset_student_progress(student_id):
    try:
        cursor.execute("""
            UPDATE student_progress
            SET completed_modules =0,
                last_activity = NULL,
                recent_activity = NULL
            WHERE student_id = %s
        """, (student_id,)
        )
        conn.commit()
        return jsonify(message="Progress reset successfully!"), 200
    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 500 
    


#ADmin section backend code

#Admin Register
@app.route("/admin/register", methods=["POST"])
def admin_register():
    data = request.get_json()
    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")

    if not all([fullname, email, password]):
        return jsonify(error="All fields are required."), 400

    hashed_password = generate_password_hash(password)

    try:
        cursor.execute("""
            INSERT INTO admins (fullname, email, password)
            VALUES (%s, %s, %s) RETURNING id;
        """, (fullname, email, hashed_password))
        conn.commit()
        return jsonify(message="Admin registration successful!"), 201
    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 500

# Admin Login 
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    cursor.execute("SELECT id, password FROM admins WHERE email=%s", (email,))
    admin = cursor.fetchone()

    if admin and check_password_hash(admin[1], password):
        session["admin_id"] = admin[0]
        return jsonify({
            "message": "Admin login successful",
            "redirect": "/admin/dashboard"
        }),200
    return jsonify(error="Invalid admin credentials"), 401



@app.route("/admin/student/<int:student_id>", methods=["GET"])
def admin_view_student(student_id):
    if "admin_id" not in session:
        return redirect("/admin/login_page")

    cursor.execute("SELECT id, fullname, email, skills, course FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
    if not student:
        return "Student not found", 404

    cursor.execute("""
        SELECT course_type, completed_modules, last_activity, COALESCE(recent_activity, '{}')
        FROM student_progress WHERE student_id=%s
    """, (student_id,))
    progress = cursor.fetchall()

    return render_template("admin_student_activity.html", student=student, progress=progress)


#Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
