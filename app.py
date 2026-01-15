from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from functools import wraps
import streamlit as st

app = Flask(__name__)
app.secret_key = "elite_academia_pro_max_2026"

# Database Configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(current_dir, 'students.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

# Auth Protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---
@app.route('/')
def home(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True
            session['username'] = user.username.upper()
            flash("Login Successful!", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials", "error")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(username=request.form.get('username'), password=hashed_pw)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Account Created Successfully!", "success")
            return redirect(url_for('login'))
        except:
            flash("Username already exists!", "error")
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    students = Student.query.all()
    return render_template('dashboard.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            new_s = Student(
                student_id=request.form.get('student_id'), name=request.form.get('name'),
                email=request.form.get('email'), phone=request.form.get('phone'),
                department=request.form.get('department'), cgpa=float(request.form.get('cgpa'))
            )
            db.session.add(new_s)
            db.session.commit()
            flash("Student Added!", "success")
            return redirect(url_for('dashboard'))
        except:
            db.session.rollback()
            flash("Error: Duplicate ID", "error")
    return render_template('add_student.html')

@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.email = request.form.get('email')
        student.phone = request.form.get('phone')
        student.department = request.form.get('department')
        student.cgpa = float(request.form.get('cgpa'))
        db.session.commit()
        flash("Record Updated!", "success")
        return redirect(url_for('dashboard'))
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:id>')
@login_required
def delete_student(id):
    s = Student.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Record Deleted!", "success")
    return redirect(url_for('dashboard'))

@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if file:
        try:
            df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
            for _, row in df.iterrows():
                new_s = Student(student_id=str(row['ID']), name=row['Name'], email=row['Email'],
                                phone=str(row['Phone']), department=row['Dept'], cgpa=float(row['GPA']))
                db.session.add(new_s)
            db.session.commit()
            flash("Data Imported Successfully!", "success")
        except: flash("File Format Error! Check Columns.", "error")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':

    app.run(debug=True)
