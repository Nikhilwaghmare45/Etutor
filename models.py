from app import db
from flask_login import UserMixin
import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    progress = db.relationship('UserProgress', backref='user', uselist=False)
    course_progress = db.relationship('CourseProgress', backref='user')
    test_results = db.relationship('TestResult', backref='user')

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_complete = db.Column(db.Boolean, default=True)
    recommended_course = db.Column(db.String(100), nullable=False)
    assessment_score_python = db.Column(db.Integer, default=0)
    assessment_score_data_analytics = db.Column(db.Integer, default=0)
    assessment_score_full_stack = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class CourseProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    current_chapter = db.Column(db.Integer, default=1)
    completed = db.Column(db.Boolean, default=False)
    started_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_name', name='unique_user_course'),
    )

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)  # Track the attempt number
    consecutive_failures = db.Column(db.Integer, default=0)  # Track consecutive failures
    is_locked = db.Column(db.Boolean, default=False)  # Track if chapter is locked due to failures
    taken_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Remove the unique constraint to allow multiple test attempts
    # and add a method to get the latest result
    @classmethod
    def get_latest_result(cls, user_id, course_name, chapter_id):
        """Get the latest test result for a user, course, and chapter"""
        return cls.query.filter_by(
            user_id=user_id,
            course_name=course_name,
            chapter_id=chapter_id
        ).order_by(cls.taken_on.desc()).first()
