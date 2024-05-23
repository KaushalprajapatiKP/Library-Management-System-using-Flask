#Module Imports
from flask import Flask, render_template, request, url_for, redirect, flash, send_file, session
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from datetime import datetime, timedelta
import secrets as secrets
import os
from gtts import gTTS
from models import db, Student, Books, Sections, BookRequest, BookReview
from werkzeug.utils import secure_filename
from flask_restful import Api
from api import BooksAPI, SectionAPI

#Initializations
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///Library_Management_System.db'
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db.init_app(app)
api = Api(app)
app.app_context().push()
login_manager = LoginManager(app)
login_manager.login_view = 'home_page'

#login Manager
@login_manager.user_loader
def load_student(id):
    return db.session.query(Student).get(int(id))

#Home Page
@app.route('/')
def home_page():
    return render_template('home_page.html')

#student login page
@app.route('/login')
def login():
    return render_template('student_login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username =request.form.get('username')
    password =request.form.get('password')
    user = Student.query.filter_by(username=username).first()
    if username == "":
        flash('Please enter your username!')
    if password == "":
        flash('Please enter your password!')
    if not user or not user.check_password(password):
        flash('Username or password is incorrect!')
        return redirect(url_for('login'))
    login_user(user)
    return redirect(url_for('student_dashboard'))

#student registration page
@app.route('/register')
def register():
    return render_template('student_registration.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password =request.form.get('password')
    name =request.form.get('name')
    surname = request.form.get('surname')
    date_of_birth = request.form.get('dob')
    gender = request.form.get('gender')
    roll_no=request.form.get('rollno')
    if Student.query.filter_by(username=username).first():
        flash('Student with this Username already exists! Please choose different username!')
        return redirect(url_for('register'))
    if Student.query.filter_by(rollno=roll_no).first():
        flash('Student with this Roll Number already exists!')
        return redirect(url_for('register'))
    user = Student(username=username, save_password=password, name=name, surname=surname, dateofbirth=datetime.strptime(date_of_birth, '%Y-%m-%d'), gender=gender, rollno=roll_no)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login'))

#librarian login page
@app.route('/librarian_login')
def librarian_login():
    return render_template('librarian_login.html')

@app.route('/librarian_login', methods=['POST'])
def librarian_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = Student.query.filter_by(username=username).first()
    if username == "Librarian" and password == "Librarian@123":
        login_user(user)
        return redirect(url_for('librarian_dashboard'))
    else:
        flash('Please enter Correct Username or Password!')
        return redirect(url_for('librarian_login'))

#logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_page'))

#librarian dashboard
@app.route('/librarian_dashboard', methods=['GET', 'POST'])
@login_required
def librarian_dashboard():
    user = current_user
    sections_list = Sections.query.filter_by().all()
    return render_template('librarian_dashboard.html', user=user, sections=sections_list)

#librarian add section
@app.route('/librarian_dashboard/add_section', methods=['GET','POST'])
@login_required
def librarian_dashboard_add_section():
    user = current_user
    if request.method   == 'POST':
        section_title = request.form.get('title')
        section_date_created = request.form.get('date_created')
        section_description = request.form.get('description')
        if section_title == "":
            flash('Please enter Section Title!')
            return redirect(url_for('librarian_dashboard_add_section'))
        if section_date_created == "":
            flash('Please enter Section Date Created!')
            return redirect(url_for('librarian_dashboard_add_section'))
        if section_description == "":
            flash('Please enter Section Description!')
            return redirect(url_for('librarian_dashboard_add_section'))
        if Sections.query.filter_by(name = section_title).first():
            flash(f'Section Title: {section_title} already exists!')
            return redirect(url_for('librarian_dashboard_add_section'))
        else:
            section = Sections(name =section_title, description =section_description, date_created = datetime.strptime((section_date_created), '%Y-%m-%d').date())
            db.session.add(section)
            db.session.commit()
            flash(f'{section.name} added successfully!')
            return redirect(url_for('librarian_dashboard'))
    return render_template('add_section.html', user=user)

#librarian edit section 
@app.route('/librarian_dashboard/edit_section/<int:section_id>', methods=['GET', 'POST'])
@login_required
def edit_section(section_id):
    user = current_user
    section = Sections.query.filter_by(id=section_id).first()
    if request.method == 'POST':
        section.name=request.form.get('title')
        section.description=request.form.get('description')
        section.date_created=section.date_created
        db.session.commit()
        flash('Section updated successfully!')
        return redirect(url_for('librarian_dashboard'))
    return render_template('edit_section.html', section=section, user=user)

#librarian delete section
@app.route('/delete_section/<int:section_id>', methods=['GET','POST'])
@login_required
def delete_section(section_id):
    user = current_user
    section = Sections.query.filter_by(id=section_id).first()
    books = Books.query.filter_by(section_id=section_id).count()
    if books >= 1:
        flash('Section cannot be deleted as it is having books!')
        return redirect(url_for('librarian_dashboard'))
    else:
        db.session.delete(section)
        db.session.commit()
        all_sections = Sections.query.all()
        for index, section in enumerate(all_sections, start=1):
            section.id = index
        db.session.commit()
        flash(f'Section {section.name} deleted successfully!', 'success')
        return redirect(url_for('librarian_dashboard', user=user))

#librarian add books
@app.route('/librarian_dashboard/add_books', methods=['GET','POST'])
@login_required
def add_books_post():
    user = current_user
    sections = Sections.query.all()
    if request.method == 'POST':
        book_title = request.form.get('title')
        book_author_1 = request.form.get('author_1')
        book_author_2 = request.form.get('author_2')
        book_author_3 = request.form.get('author_3')
        book_content = request.form.get('content')
        book_section_id = int(request.form.get('section_id')) 
        book_pdf = request.files.get('pdf')
        issue_date = datetime.utcnow() + timedelta(hours=5, minutes=30)
        return_date = issue_date + timedelta(days=21)
        
        if not all([book_title, book_author_1, book_content, book_section_id]):
            flash('Please enter all details of book!')
            return redirect(url_for('add_books_post'))

        if book_pdf:
            pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(book_pdf.filename))
            book_pdf.save(pdf_filename)
        else:
            pdf_filename = None
        book = Books(book_name=book_title, author_1=book_author_1, author_2=book_author_2, author_3=book_author_3 , content=book_content, section_id=book_section_id, return_date=return_date, issue_date=issue_date, pdf=pdf_filename)
        db.session.add(book)
        db.session.commit()
        flash(f'Book {book_title} added successfully!')
        return redirect(url_for('librarian_dashboard'))
    return render_template('add_books.html', sections=sections, user=user)

#librarian pending book requests
@app.route('/librarian_dashboard/pending_requests')
@login_required
def pending_requests():
    user = current_user
    pending_requests = db.session.query(BookRequest, Student, Books)\
            .join(Student, BookRequest.student_id == Student.id)\
            .join(Books, BookRequest.book_id == Books.id)\
            .filter(BookRequest.status == 'pending')\
            .all()
    return render_template('pending_requests.html', pending_requests=pending_requests, user=user)

#librarian update book request status (approve/reject)
@app.route('/update_request_status/<int:request_id>', methods=['POST' ])
@login_required
def update_request_status(request_id):
    user = current_user
    request_status = request.form.get("status")
    book_request = BookRequest.query.get(request_id)
    book_id = book_request.book_id
    book = Books.query.get(book_id)
    if request_status == 'declined':
        book.requested = False
    if request_status == 'granted':
        book.issue_date = datetime.utcnow() + timedelta(hours=5, minutes=30)
    book_request.status = request_status
    db.session.commit()
    flash('Request status updated successfully!')
    return redirect(url_for('pending_requests', user=user))

#librarian section 
@app.route('/librarian_dashboard/section/<int:section_id>', methods=['GET','POST'])
@login_required
def section_page(section_id):
    user = current_user
    section = Sections.query.filter_by(id=section_id).first()
    books = Books.query.filter_by(section_id=section_id).all()
    return render_template('section.html', section=section, books=books, user=user)

#librarian delete book
@app.route('/delete_book/<int:book_id>', methods=['GET','POST'])
@login_required
def delete_book(book_id):
    user = current_user
    book = Books.query.filter_by(id=book_id).first()
    book_request = BookRequest.query.filter_by(book_id=book_id).first()
    if book_request:
        db.session.delete(book_request)
        db.session.commit()
    db.session.delete(book)
    db.session.commit()
    all_books = Sections.query.all()
    for index, section in enumerate(all_books, start=1):
        section.id = index
    db.session.commit()
    flash(f'Book {book.book_name} deleted successfully!', 'success')
    return redirect(url_for('librarian_dashboard', user=user))

#librarian edit book
@app.route('/librarian_dashboard/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    user=current_user
    book = Books.query.filter_by(id=book_id).first()
    sections = Sections.query.all()
    if request.method == 'POST':
        book.book_name=request.form.get('book_name')
        book.author_1=request.form.get('author_1')
        book.author_2=request.form.get('author_2')
        book.author_3=request.form.get('author_3')
        book.content=request.form.get('content')
        book.section_id=int(request.form.get('section_id'))
        book_pdf = request.files.get('pdf')
        if book_pdf:
            filename = secure_filename(book_pdf.filename)
            book_pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            book.pdf= filename
        db.session.commit()
        flash('Book updated successfully!')
        return redirect(url_for('librarian_dashboard', user=user))
    return render_template('edit_book.html', book=book, sections=sections, user=user)

#librarian search book 
@app.route('/search_books' , methods=['GET','POST'])
@login_required
def search_books():
    user = current_user
    books = []
    filter_by = request.form.get('filter', 'all')
    query = request.form.get('query').capitalize()
    if filter_by == 'book_name' and query != "":
        books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).filter(Books.book_name == query).all()
    elif filter_by == 'author' and query != "":
        books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).filter(Books.author_1 == query).all()
    elif filter_by == 'section' and query != "":
        section = Sections.query.filter_by(name = query).first()
        if section:
            section_id = section.id
            books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).filter(Sections.id == section_id).all()
    elif filter_by == 'all' and query != "":
        books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).all()
    else:
        books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).all()
    return render_template('search_books.html', books=books, user=user)

#librarian stats regarding books     
@app.route('/librarian_dashboard/librarian_stats', methods=['GET', 'POST'])
@login_required
def librarian_stats():
    user = current_user
    books_data = db.session.query(BookRequest, Student, Books)\
            .join(Student, BookRequest.student_id == Student.id)\
            .join(Books, BookRequest.book_id == Books.id)\
            .filter(BookRequest.status.in_(['granted']))\
            .all()
    student_data = Student.query.all()
    books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).all()
    return render_template('librarian_stats.html', books_data=books_data, books=books, student_data=student_data, user=user)

#librarian revoke book permission
@app.route('/revoke_permission/<int:book_id>', methods=['POST', 'GET'])
@login_required
def revoke_permission(book_id):
    user = current_user
    book = Books.query.get(book_id)
    book_requests = BookRequest.query.filter_by(book_id=book_id).all()
    book_requests = [book for book in book_requests if book.status =='granted']
    if book:
        book.requested = False
        book_requests[0].status = 'declined'
        db.session.commit()
        flash('Book permission revoked!', 'success')
    else:
        flash('Book not found!', 'error')
    return redirect(url_for('librarian_stats', user=user))  

#student dashboard
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    user = current_user
    books_data = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).all()
    return render_template('student_dashboard.html', user=user, books = books_data)

#student edit profile 
@app.route('/student_dashboard/edit_profile', methods=['POST', 'GET'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        username = request.form.get('username')
        c_password = request.form.get('c_password')
        n_password = request.form.get('n_password')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        roll_no = request.form.get('rollno')
        name = request.form.get('name')
        surname = request.form.get('surname')
        student = Student.query.filter_by(rollno=roll_no, username=username).first()
        if student:
            if user.check_password(c_password):
                student.name = name
                student.surname = surname
                student.dateofbirth=datetime.strptime(dob, '%Y-%m-%d')
                student.gender = gender
                if n_password:
                    student.save_password = n_password
                    flash('Password changed!')
                db.session.commit()
                flash('Profile updated successfully!')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Incorrect password. Please try again.')
        else:
            flash('No student found with the provided username and roll number.')
    
    return render_template('edit_profile.html', user=user)

#student request books
@app.route('/request_book/<int:book_id>', methods=['POST'])
@login_required
def request_book(book_id):
    student = current_user
    existing_bookRequest = BookRequest.query.filter_by(student_id=student.id, book_id=book_id, status="pending").first()
    if not existing_bookRequest:
        if BookRequest.query.filter_by(student_id=student.id).filter(BookRequest.status.in_(['granted', 'pending'])).count() < 5:
            book_request = BookRequest(student_id=student.id, book_id=book_id, status='pending')
            db.session.add(book_request)
            db.session.commit()
            book = Books.query.filter_by(id=book_id).first()
            book.requested = True
            db.session.commit()
            flash('Book request submitted successfully!')
        else:
            flash('You Have requested more books than allowed limit!')
    else:
        flash('You have already requested this book!')
    return redirect(url_for('all_books'))

#student all books
@app.route('/student_dashboard/all_books', methods=['GET'])
@login_required
def all_books():
    user = current_user
    ratings = {}
    books = Books.query.all()
    for book in books:
        ratings[book.id] = calculate_average_ratings(book.id)
    payment_status = session.get('payment_status', {})
    payment_status = {int(k): v for k, v in payment_status.items()}
    books = db.session.query(Books, Sections).join(Sections, Books.section_id == Sections.id).all()
    return render_template('all_books.html', books=books, user=user, payment_status=payment_status, ratings=ratings)

#student my books
@app.route('/student_dashboard/my_books',methods=['GET', 'POST'])
@login_required
def my_books():
    user = current_user
    books = db.session.query(BookRequest, Books, Sections)\
            .join(Books, BookRequest.book_id == Books.id)\
            .join(Sections, Books.section_id == Sections.id)\
            .filter(BookRequest.status.in_(['granted']), BookRequest.student_id == user.id)\
            .all()
    pending_books = db.session.query(BookRequest, Books, Sections)\
            .join(Books, BookRequest.book_id == Books.id)\
            .join(Sections, Books.section_id == Sections.id)\
            .filter(BookRequest.status.in_(['pending']), BookRequest.student_id == user.id)\
            .all()
    payment_status = session.get('payment_status', {})
    payment_status = {int(k): v for k, v in payment_status.items()}
    return render_template('my_books.html', books=books, user=user, pending_books=pending_books, payment_status=payment_status)

#student book reviews
@app.route('/student_dashboard/my_books/review_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def review_book(book_id):
    user = current_user
    book = Books.query.filter_by(id=book_id).first()
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        student_id = request.form.get('student_id')
        rating = int(request.form.get('rating'))
        review_text = request.form.get('review_text')
        review = BookReview(book_id=book_id, student_id=student_id, rating=rating, review_text=review_text)
        db.session.add(review)
        db.session.commit()
        flash('Your book review is registered Successfully!')
        return redirect(url_for('my_books'))
    return render_template('review_book.html', user=user, book=book)

#student book payment gateway
@app.route('/student_dashboard/payment_gateway/<int:book_id>', methods=['GET'])
def payment_gateway(book_id):
    book = Books.query.filter_by(id=book_id).first()
    return render_template('payment_gateway.html', book=book)

#student credit debit card payment option 
@app.route('/credit_debit_payment/<int:book_id>', methods=['GET', 'POST'])
def credit_debit_payment(book_id):
    user = current_user
    payment_status = session.get('payment_status', {})
    payment_status = {int(k): v for k, v in payment_status.items()}
    if request.method == 'POST':
        payment_status[book_id] = True 
        session['payment_status'] = payment_status
        session.modified = True
        return redirect(url_for('all_books'))
    return render_template('credit_debit.html', user=user, book_id=book_id)

#student upi payment option
@app.route('/upi_payment/<int:book_id>', methods=['GET', 'POST'])
def upi_payment(book_id):
    user = current_user
    payment_status = session.get('payment_status', {})
    payment_status = {int(k): v for k, v in payment_status.items()}
    if request.method == 'POST':
        payment_status[book_id] = True 
        session['payment_status'] = payment_status
        session.modified = True
        return redirect(url_for('all_books'))
    return render_template('upi.html', book_id=book_id, payment_status=payment_status, user=user)

#student process payment
@app.route('/process_payment/<int:book_id>', methods=['POST'])
def process_payment(book_id):
    payment_method = request.form['payment_method']
    if payment_method == 'debit_card' or payment_method == 'credit_card':
        return redirect(url_for('credit_debit_payment', book_id=book_id))
    else:
        return redirect(url_for('upi_payment', book_id=book_id))
    
#student book pdf download after payment   
@app.route('/initiate_download/<int:book_id>', methods=['GET'])
def initiate_download(book_id):
    book = Books.query.get(book_id)
    book_pdf = book.pdf
    if book and book_pdf:
        if os.path.exists(book_pdf):
            # flash(f'PDF of {book.book_name}  downloaded successfully!')
            return(send_file(book_pdf, as_attachment=True))
        else:
            flash('PDF of this Book is not available!')  
    else:
        flash('PDF of this Book is not available!')
        return redirect(url_for('student_dashboard'))
    
#average book rating calculation
def calculate_average_ratings(book_id):
    latest_reviews = BookReview.query.filter_by(book_id=book_id).order_by(BookReview.submition_time.desc()).all()
    latest_ratings = {}
    for review in latest_reviews:
        latest_ratings[review.student_id] = review.rating
    if len(latest_ratings) == 0:
        return "No ratings"
    else:
        total_sum = sum(latest_ratings.values())
        average_rating = total_sum / len(latest_ratings)
        return average_rating
    
#student book audio converter
@app.route('/text_to_speech/<int:book_id>')
def text_to_speech(book_id):
    book = Books.query.join(Sections, Books.section_id == Sections.id).filter(Books.id == book_id).first()
    book_details = f"Title: {book.book_name}. Author: {book.author_1}. Section: {book.section.name}. Content: {book.content}"
    tts = gTTS(text=book_details, lang='en')
    audio_file_path = f'audio_output_{book_id}.mp3'
    tts.save(audio_file_path)
    return send_file(audio_file_path, as_attachment=True)

#api
api.add_resource(BooksAPI,"/api/book", "/api/book/<int:book_id>")
api.add_resource(SectionAPI,"/api/section", "/api/section/<int:section_id>")

#initialization
with app.app_context():
    db.create_all() 
    librarian = Student.query.filter_by(username='Librarian').first()
    if not librarian:
        librarian = Student(username='Librarian', save_password = 'Librarian@123', is_librarian = True, name = 'Librarian',surname='Librarian', dateofbirth = datetime.strptime('1998-12-6', '%Y-%m-%d'), gender = 'Male', rollno=123)
        db.session.add(librarian)
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
