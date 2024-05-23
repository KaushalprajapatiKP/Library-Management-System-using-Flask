#Module Imports
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, timezone

#Initialization
db = SQLAlchemy()

#student table
class Student(db.Model, UserMixin):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String[32],unique=True, nullable=False)
    passhash = db.Column(db.String[512],nullable=False)
    name = db.Column(db.String[64],nullable=False)
    surname = db.Column(db.String[64],nullable=False)
    dateofbirth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String[16], nullable=False)
    is_librarian = db.Column(db.Boolean, default=False)
    rollno = db.Column(db.String[64], nullable=False, unique=True)


    def check_password(self, password):
        return check_password_hash(self.passhash, password)
    
    @property
    def password(self):
        raise AttributeError('You cannot read the password attribute!')

    @password.setter
    def save_password(self, password):
        self.passhash = generate_password_hash(password)


#section table
class Sections(db.Model):
    __tablename__ ='sections'
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    date_created = db.Column(db.Date, nullable=False, default=(datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)))
    description = db.Column(db.String(1080), nullable=False)

#books table
class Books(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    book_name = db.Column(db.String(64), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=True)
    author_1 = db.Column(db.String(64), nullable=False)
    author_2 = db.Column(db.String(64), nullable=True)
    author_3 = db.Column(db.String(64), nullable=True)
    pdf = db.Column(db.String(64), nullable=True)
    issue_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(hours=5, minutes=30))
    return_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(days=21) + timedelta(hours=5, minutes=30))
    requested = db.Column(db.Boolean, default=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    section = db.relationship('Sections',backref=db.backref('books', lazy=True))
    
#book requests table 
class BookRequest(db.Model):
    __tablename__= 'book requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    request_date = db.Column(db.DateTime, default=datetime.now(timezone.utc) + timedelta(hours=5, minutes=30))

#book reviews table
class BookReview(db.Model):
    __tablename__ = 'book reviews'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    submition_time = db.Column(db.TIMESTAMP, default=datetime.now(timezone.utc) + timedelta(hours=5, minutes=30), nullable=False)

