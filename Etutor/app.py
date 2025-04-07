import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
from sqlalchemy.orm import DeclarativeBase
import pandas as pd

# Create the Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG level to see debug messages
app.logger.setLevel(logging.DEBUG)

# Define the evaluate_test_result function
def evaluate_test_result(answers, questions):
    score = 0
    correct_answers = 0
    total_questions = len(questions)

    for question in questions:
        if answers.get(str(question["id"])) == question["correct_option"]:
            correct_answers += 1

    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score >= 60  # Assuming 60% is the passing score
    return score, passed

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app.secret_key = os.environ.get("SESSION_SECRET", "insecure-dev-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///new_lms.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import User, UserProgress, CourseProgress, TestResult
from chatbot import get_chatbot

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def load_mcq_data(course_name):
    try:
        filename = f'data/new_{course_name}.json'  # Updated to use new filenames
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.error(f"{filename} not found")
        return None
    except json.JSONDecodeError:
        app.logger.error(f"Invalid JSON in {filename}")
        return None

with app.app_context():
    db.create_all()

def load_course_data():
    try:
        with open('data/courses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.warning("courses.json not found, generating default data")
        courses = {
            "python": {"title": "Python Programming", "description": "Learn Python programming from basics to advanced concepts", "chapters": []},
            "data_analytics": {"title": "Data Analytics", "description": "Master data analysis techniques and tools", "chapters": []},
            "full_stack": {"title": "Full Stack Development", "description": "Become a full stack web developer with front-end and back-end skills", "chapters": []}
        }
        for course_key in courses:
            for i in range(1, 10):
                chapter_content = f"This is the content for chapter {i} of the {courses[course_key]['title']} course."
                courses[course_key]["chapters"].append({
                    "id": i,
                    "title": f"Chapter {i}: {course_key.replace('_', ' ').title()} Fundamentals {i}",
                    "content": chapter_content,
                    "test": f"test_{course_key}_{i}"
                })
        with open('data/courses.json', 'w') as f:
            json.dump(courses, f, indent=4)
        return courses

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    from forms import RegistrationForm
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_password,
            age=form.age.data,
            degree=form.degree.data,
            branch=form.branch.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    from forms import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user_progress = UserProgress.query.filter_by(user_id=user.id).first()
            if not user_progress:
                return redirect(url_for('assessment'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    from assessment import load_assessment_data, generate_assessment_questions, evaluate_assessment
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).first()
    if user_progress:
        flash('You have already completed the assessment', 'info')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        answers = request.form.to_dict()
        data_analytics, full_stack, python = load_assessment_data()
        scores = evaluate_assessment(answers, data_analytics, full_stack, python)
        recommended_course = max(scores, key=lambda k: scores[k])
        from ml_assessment import evaluate_assessment_with_ml
        recommended_chapters = evaluate_assessment_with_ml(scores)
        user_progress = UserProgress(
            user_id=current_user.id,
            recommended_course=recommended_course,
            assessment_score_python=scores['Python'],
            assessment_score_data_analytics=scores['Data Analytics'],
            assessment_score_full_stack=scores['Full Stack']
        )
        db.session.add(user_progress)
        courses = ['python', 'data_analytics', 'full_stack']
        for course in courses:
            current_chapter = recommended_chapters.get(course, 1)
            course_progress = CourseProgress(
                user_id=current_user.id,
                course_name=course,
                current_chapter=current_chapter,
                completed=False
            )
            db.session.add(course_progress)
        db.session.commit()
        flash('Assessment completed! Your personalized learning path is ready.', 'success')
        return redirect(url_for('dashboard'))
    data_analytics, full_stack, python = load_assessment_data()
    questions = generate_assessment_questions(data_analytics, full_stack, python)
    return render_template('assessment.html', questions=questions)

@app.route('/dashboard')
@login_required
def dashboard():
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).first()
    if not user_progress:
        return redirect(url_for('assessment'))
    course_progress = CourseProgress.query.filter_by(user_id=current_user.id).all()
    progress_data = {}
    for progress in course_progress:
        percentage = ((progress.current_chapter - 1) / 9) * 100
        progress_data[progress.course_name] = {
            'current_chapter': progress.current_chapter,
            'percentage': percentage,
            'completed': progress.completed
        }
    courses = load_course_data()
    # Normalize recommended_course to match courses.json keys
    recommended_course_normalized = user_progress.recommended_course.lower().replace(' ', '_')
    return render_template(
        'dashboard.html',
        user=current_user,
        progress=user_progress,
        course_progress=progress_data,
        courses=courses,
        recommended_course=recommended_course_normalized  # Pass normalized value
    )

@app.route('/course/<course_name>')
@login_required
def course(course_name):
    courses = load_course_data()
    if course_name not in courses:
        flash('Course not found', 'danger')
        return redirect(url_for('dashboard'))
    course_progress = CourseProgress.query.filter_by(user_id=current_user.id, course_name=course_name).first()
    if not course_progress:
        course_progress = CourseProgress(user_id=current_user.id, course_name=course_name, current_chapter=1, completed=False)
        db.session.add(course_progress)
        db.session.commit()
    current_chapter = course_progress.current_chapter
    course_data = courses[course_name]
    return render_template('course.html', course_name=course_name, course=course_data, current_chapter=current_chapter)
@app.route('/chapter/<course_name>/<int:chapter_id>')
@login_required
def chapter(course_name, chapter_id):
    courses = load_course_data()
    if course_name not in courses or chapter_id < 1 or chapter_id > len(courses[course_name]['chapters']):
        flash('Chapter not found', 'danger')
        return redirect(url_for('course', course_name=course_name))

    # Check user's progress
    course_progress = CourseProgress.query.filter_by(user_id=current_user.id, course_name=course_name).first()
    if not course_progress or chapter_id > course_progress.current_chapter:
        flash('You need to complete previous chapters first', 'warning')
        return redirect(url_for('course', course_name=course_name))

    chapter_data = courses[course_name]['chapters'][chapter_id - 1]
    chatbot_initialized = get_chatbot(courses)
    return render_template(
        'chapter.html',
        course_name=course_name,
        chapter=chapter_data,
        course=courses[course_name],
        chatbot_enabled=True,
        current_chapter_id=chapter_id
    )

@app.route('/test/<course_name>/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def chapter_test(course_name, chapter_id):
    courses = load_course_data()
    if course_name not in courses or chapter_id < 1 or chapter_id > len(courses[course_name]['chapters']):
        flash('Test not found', 'danger')
        return redirect(url_for('course', course_name=course_name))
    
    course_progress = CourseProgress.query.filter_by(user_id=current_user.id, course_name=course_name).first()
    if not course_progress or chapter_id > course_progress.current_chapter:
        flash('You need to complete previous chapters first', 'warning')
        return redirect(url_for('course', course_name=course_name))
    
    chapter_data = courses[course_name]['chapters'][chapter_id - 1]
    latest_result = TestResult.get_latest_result(current_user.id, course_name, chapter_id)
    if latest_result and latest_result.is_locked:
        flash('This chapter is locked due to consecutive test failures.', 'warning')
        return redirect(url_for('chapter', course_name=course_name, chapter_id=chapter_id-1) if chapter_id > 1 else url_for('course', course_name=course_name))
    
    concepts = load_concepts_data()
    if concepts is None:
        app.logger.error(f"Failed to load concepts for {course_name} Chapter {chapter_id}")
        flash("Error loading test data. Please try again later.", "danger")
        return redirect(url_for('course', course_name=course_name))
    
    try:
        # Generate questions once and store them for consistency
        questions = generate_nlp_test(chapter_data['content'], chapter_id, course_name, concepts)
        
        if request.method == 'POST':
            answers = request.form.to_dict()
            app.logger.debug(f"Submitted Answers: {answers}")
            score, passed = evaluate_test_result(answers, questions)
            
            # Add this line here to log the questions after evaluation
            app.logger.debug(f"Questions: {questions}")
            app.logger.debug(f"Test Result - Score: {score}, Passed: {passed}, Answers: {answers}")
            
            attempt_number = 1
            consecutive_failures = 0
            is_locked = False
            previous_results = TestResult.query.filter_by(user_id=current_user.id, course_name=course_name, chapter_id=chapter_id).order_by(TestResult.taken_on.desc()).all()
            
            if previous_results:
                latest_result = previous_results[0]
                attempt_number = latest_result.attempt_number + 1
                if not latest_result.passed:
                    consecutive_failures = latest_result.consecutive_failures + 1
                    if chapter_id > 1 and consecutive_failures >= 2:
                        is_locked = True
                        flash('Chapter locked due to consecutive failures.', 'danger')
                else:
                    consecutive_failures = 0
            
            if passed:
                consecutive_failures = 0
                is_locked = False
            
            test_result = TestResult(
                user_id=current_user.id,
                course_name=course_name,
                chapter_id=chapter_id,
                score=score,
                passed=passed,
                attempt_number=attempt_number,
                consecutive_failures=consecutive_failures,
                is_locked=is_locked
            )
            db.session.add(test_result)
            
            if passed and course_progress.current_chapter == chapter_id:
                course_progress.current_chapter += 1
                if course_progress.current_chapter > len(courses[course_name]['chapters']):
                    course_progress.completed = True
            
            db.session.commit()
            
            if is_locked:
                return redirect(url_for('chapter', course_name=course_name, chapter_id=chapter_id-1) if chapter_id > 1 else url_for('course', course_name=course_name))
            elif passed:
                flash(f'Test passed! Score: {score:.2f}%', 'success')
                return redirect(url_for('chapter', course_name=course_name, chapter_id=chapter_id + 1) if chapter_id < len(courses[course_name]['chapters']) else url_for('course', course_name=course_name))
            else:
                flash(f'Test failed. Score: {score:.2f}%. Need 60% to pass.', 'danger')
                return redirect(url_for('chapter', course_name=course_name, chapter_id=chapter_id))
        
        return render_template('test.html', course_name=course_name, chapter_id=chapter_id, questions=questions, chapter=chapter_data)
    except Exception as e:
        app.logger.error(f"Error in chapter_test: {str(e)}")
        flash("An unexpected error occurred while loading the test.", "danger")
        return redirect(url_for('course', course_name=course_name))
    


@app.route('/api/progress')
@login_required
def api_progress():
    course_progress = CourseProgress.query.filter_by(user_id=current_user.id).all()
    progress_data = {}
    for progress in course_progress:
        percentage = ((progress.current_chapter - 1) / 9) * 100  # Assuming 9 chapters per course
        progress_data[progress.course_name] = {
            'current_chapter': progress.current_chapter,
            'percentage': percentage,
            'completed': progress.completed
        }
    return jsonify(progress_data)



@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request, no data provided"}), 400
        user_message = data.get('message', '').strip()
        course_name = data.get('course_name', '')
        chapter_id = data.get('chapter_id', None)
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        courses = load_course_data()
        chatbot = get_chatbot(courses)
        chapter_id = int(chapter_id) if chapter_id else None
        response = chatbot.get_response(user_message, course_name, chapter_id)
        return jsonify({"response": response, "course_name": course_name, "chapter_id": chapter_id})
    except Exception as e:
        app.logger.error(f"Chatbot API error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def initialize_app():
    if not os.path.exists('data'):
        os.makedirs('data')
    csv_files = [
        ('data_analytics_new.csv', 'data/data_analytics_new.csv'),
        ('full_stack_new.csv', 'data/full_stack_new.csv'),
        ('python_new.csv', 'data/python_new.csv')
    ]
    for src, dest in csv_files:
        if not os.path.exists(dest):
            try:
                src_path = f'attached_assets/{src}'
                if os.path.exists(src_path):
                    df = pd.read_csv(src_path)
                    df.to_csv(dest, index=False)
            except Exception as e:
                logging.error(f"Error copying data file {src}: {e}")

with app.app_context():
    initialize_app()