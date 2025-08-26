from flask import Flask, request, jsonify
import psycopg2
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
bcrypt = Bcrypt(app)

CORS(app)

# Database connection
conn = psycopg2.connect(
    dbname="progress",
    user="postgres",
    password="2003",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Route for registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    fullname = data['fullname']
    email = data['email']
    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    skills = data['skills']
    course = data['course']
    resume = data['resume']
    info = data['info']

    try:
        cursor.execute("""
            INSERT INTO students (fullname, email, password, skills, course, resume, info)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fullname, email, password, skills, course, resume, info))
        conn.commit()
        return jsonify({"message": "Registration successful!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Route for login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    try:
        conn = psycopg2.connect(
            database="progress",
            user="postgres",
            password="2003",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT password, course FROM students WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[0], password):
            return jsonify({"message": "Login successful!", "course": user[1]})
        else:
            return jsonify({"error": "Invalid email or password"}), 401
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
