from flask import Flask, render_template,url_for,flash,redirect,request,session,jsonify
from datetime import datetime,date,timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request
from flask_mail import Mail, Message

app = Flask(__name__)

# Configuring Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'winwinhtet199977@gmail.com'
app.config['MAIL_PASSWORD'] = 'othc lisz ewrx ducd'

mail = Mail(app)

app.config['SECRET_KEY'] = 'winwinhtet'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:toor@localhost:5432/Thesis'
db = SQLAlchemy(app)
app.app_context().push()

class Admin(db.Model):
    admin_id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100),nullable=False)

class User(db.Model):
    user_id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    isEmployee = db.Column(db.Boolean, nullable=False)

    # One-to-One relationship with Profile
    profile = db.relationship('Profile', backref='user', uselist=False)

    # One-to-Many relationship with Job_Offer_Post
    job_offer_posts = db.relationship('Job_Offer_Post', backref='user', lazy=True)

    # One-to-Many relationship with JobAlert
    job_alerts = db.relationship('JobAlert', backref='user', lazy=True)

    # One-to-Many relationship with FeedBack
    feedbacks = db.relationship('FeedBack', backref='user', lazy=True)


class Profile(db.Model):
    user_profile_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer(), nullable=True)
    gender = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.String, nullable=True)
    experiences = db.Column(db.String, nullable=True)
    contact = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String, nullable=True)
    company_name = db.Column(db.String(100),nullable=True)
    about_company = db.Column(db.Text, nullable=True)

    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)


class Job_Offer_Post(db.Model):
    post_id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(200), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_date = db.Column(db.Date, default=date.today)
    deadline = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String, nullable=False)
    skill_requirement = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    edited = db.Column(db.Boolean, nullable=True, default=False)

    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)


class JobAlert(db.Model):
    job_alert_id = db.Column(db.Integer(), primary_key=True)
    job_title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    alertstatus = db.Column(db.Boolean, default=False, nullable=True)
    created_date = db.Column(db.Date, default=date.today)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)


class FeedBack(db.Model):
    feedback_id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.Text, nullable=False)

    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)


db.create_all()


# Add initial admin user
if not Admin.query.first():
    admin = Admin(username='admin', password='adminpassword')
    db.session.add(admin)
    db.session.commit()

    
@app.route('/')
def main():
    return render_template('main.html')

@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    job_offers_test = Job_Offer_Post.query.paginate(per_page=3,page=page)
    # print('total page is ',job_offers_test.page)
    # print('page iteration is ',job_offers_test.iter_pages)
    # print('items are ',job_offers_test.items)
    return render_template('home.html',title="Home Page", job_offers=job_offers_test)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/profile', methods=['GET'])
def profile():
    if not session.get('user_logged_in'):
        return redirect('/login')
    
    user_email = session.get('user_email')
    user_id = session.get('user_id')
    
    # Fetch user and profile data
    user = User.query.get(user_id)
    user_profile = Profile.query.filter_by(user_id=user_id).first()
    user_alerts = JobAlert.query.filter_by(user_email=user_email).all()
    
    return render_template('profile.html', 
                           alerts=user_alerts, 
                           profile=user_profile, 
                           is_employee=user.isEmployee)

@app.route('/setprofile', methods=['GET', 'POST'])
def setprofile():
    if not session.get('user_logged_in'):
        return redirect('/login')
    
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        # Extract profile data from the form
        name = request.form['name']
        title = request.form['title']
        age = request.form['age']
        gender = request.form['gender']
        skills = request.form['skills']
        experiences = request.form['experiences']
        contact = request.form['contact']
        contact_email = request.form['contact_email']
        address = request.form['address']
        
        # Check if a profile already exists for the user
        user_profile = Profile.query.filter_by(user_id=user_id).first()
        
        if user_profile:
            # Update existing profile
            user_profile.name = name
            user_profile.title = title
            user_profile.age = age
            user_profile.gender = gender
            user_profile.skills = skills
            user_profile.experiences = experiences
            user_profile.contact = contact
            user_profile.contact_email = contact_email
            user_profile.address = address
        else:
            # Create new profile with the user_id
            user_profile = Profile(
                name=name,
                title=title,
                age=age,
                gender=gender,
                skills=skills,
                experiences=experiences,
                contact=contact,
                contact_email=contact_email,
                address=address,
                user_id=user_id  # Make sure to assign the user_id
            )
            db.session.add(user_profile)
        
        db.session.commit()
        return redirect('/profile')
    
    return render_template('setupprofile.html')

@app.route('/setupprofile', methods=['GET', 'POST'])
def setupprofile():
    if not session.get('user_logged_in'):
        return redirect('/login')
    
    user_id = session.get('user_id')
    
    # Determine if the user is an employee or employer
    user = User.query.get(user_id)
    is_employee = user.isEmployee  # Adjust this based on how you determine user type
    
    if request.method == 'POST':
        if is_employee:
            # Extract employee profile data from the form
            name = request.form['fullName']
            title = request.form['jobTitle']
            age = request.form['age']
            gender = request.form['gender']
            skills = request.form['skills']
            experiences = request.form['experiences']
            contact = request.form['phoneNumber']
            contact_email = request.form['email']
            address = request.form['address']
            
            # Fetch or create employee profile
            user_profile = Profile.query.filter_by(user_id=user_id).first()
            
            if user_profile:
                # Update existing employee profile
                user_profile.name = name
                user_profile.title = title
                user_profile.age = int(age)
                user_profile.gender = gender
                user_profile.skills = skills
                user_profile.experiences = experiences
                user_profile.contact = contact
                user_profile.contact_email = contact_email
                user_profile.address = address
            else:
                # Create a new employee profile
                user_profile = Profile(
                    name=name,
                    title=title,
                    age=int(age),
                    gender=gender,
                    skills=skills,
                    experiences=experiences,
                    contact=contact,
                    contact_email=contact_email,
                    address=address,
                    user_id=user_id
                )
                db.session.add(user_profile)
        else:
            # Extract employer profile data from the form
            company_name = request.form['companyName']
            phone_number = request.form['phoneNumber']
            email = request.form['email']
            address = request.form['address']
            about_company = request.form['aboutCompany']
            
            # Fetch or create employer profile
            user_profile = Profile.query.filter_by(user_id=user_id).first()
            
            if user_profile:
                # Update existing employer profile
                user_profile.company_name = company_name
                user_profile.contact = phone_number
                user_profile.contact_email = email
                user_profile.address = address
                user_profile.about_company = about_company
            else:
                # Create a new employer profile
                user_profile = Profile(
                    company_name=company_name,
                    contact=phone_number,
                    contact_email=email,
                    address=address,
                    about_company=about_company,
                    user_id=user_id
                )
                db.session.add(user_profile)
        
        db.session.commit()
        return redirect(url_for('profile'))
    
    return render_template('setupprofile.html', is_employee=is_employee)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Get the user type from the form
        user_type = request.form['userType']
        
        # Set isEmployee to True if the user is an Employee, False if Employer
        is_employee = True if user_type == 'employee' else False
        
        # Create a new User object with isEmployee field set
        new_user = User(username=username, email=email, password=password, isEmployee=is_employee)
        
        # Add the new user to the session
        db.session.add(new_user)
        db.session.commit()
        
        # Fetch the user_id of the newly created user
        user_id = new_user.user_id
        
        # Automatically create a Profile for the new user
        new_profile = Profile(
            name=username,  # You can adjust this if you collect full name
            title="Title Placeholder",  # Placeholder or you can gather this in the form
            age=0,  # Placeholder age or you can gather this in the form
            gender="Not Specified",  # Placeholder gender or you can gather this in the form
            skills="",  # Placeholder skills or you can gather this in the form
            experiences="",  # Placeholder experiences or you can gather this in the form
            contact="",  # Placeholder contact or you can gather this in the form
            contact_email=email,  # Using the user's email
            address="",  # Placeholder address or you can gather this in the form
            user_id=user_id  # Link profile to user
        )
        
        db.session.add(new_profile)
        db.session.commit()
        
        return redirect('/login')

    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user is an admin
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin_logged_in'] = True
            session['admin_id'] = admin.admin_id
            return redirect('/admin')
        
        # Check if the user is a regular user
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = user.username
            session['user_id'] = user.user_id
            session['user_logged_in'] = True
            session['is_employee'] = user.isEmployee
            session['user_email'] = user.email
            return redirect('/profile')
    
    return render_template('login.html')


@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect('/login')
    return render_template('admin.html',)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in',None)
    session.pop('user_logged_in',None)
    return redirect('/home')


@app.route('/submitPost', methods=['GET', 'POST'])
def submitPost():
    if request.method == 'POST':
        job_title = request.form['title']
        username = session.get('username')
        email = request.form['email']
        age = request.form['age']
        salary = request.form['salary']
        gender = request.form['gender']
        deadline = request.form['deadline']
        address = request.form['address']
        description = request.form['description']
        phone = request.form['contact']
        skills = request.form['skills']
        job_type = request.form['job_type']
        
        # Get the user_id from the session
        user_id = session.get('user_id')  # Ensure 'user_id' is stored in session when user logs in
        
        if user_id is None:
            # Handle the case where user_id is not in session (e.g., redirect to login)
            return redirect('/login')

        new_post = Job_Offer_Post(
            job_title=job_title, 
            email=email,
            age=age,
            gender=gender,
            deadline=deadline,
            location=address,
            description=description,
            phone=phone,
            skill_requirement=skills,
            type=job_type,
            username=username,
            salary=salary,
            user_id=user_id  # Add user_id here
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect('/profile')
    return render_template('jobOffer.html')



@app.route('/submitJobAlert',methods=['GET','POST'])
def submitJobAlert():
    if request.method == 'POST':
        job_title = request.form['job_title']
        address = request.form['location']
        type = request.form['job_type']
        user_email = session.get('user_email')
        salary = request.form['salary']
        user_id = session.get('user_id') 
        job_alert = JobAlert(job_title=job_title, location=address, job_type=type,user_email=user_email,salary = salary,user_id=user_id)
        db.session.add(job_alert)
        db.session.commit()
        return redirect('/profile')
    return render_template('jobAlert.html')

@app.route('/editJobAlert/<int:job_alert_id>', methods=['GET', 'POST'])
def editJobAlert(job_alert_id):
    alert = JobAlert.query.get_or_404(job_alert_id)
    if request.method == 'POST':
        alert.job_title = request.form['job_title']
        alert.location = request.form['location']
        alert.job_type = request.form['job_type']
        alert.salary = request.form['salary']
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('editJobAlert.html', alert=alert)

@app.route('/deleteJobAlert/<int:job_alert_id>', methods=['POST'])
def deleteJobAlert(job_alert_id):
    alert = JobAlert.query.get_or_404(job_alert_id)
    db.session.delete(alert)
    db.session.commit()
    return redirect(url_for('profile'))

def send_email(recipient, subject, body):
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
    msg.body = body

    try:
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        return str(e)

def get_cosine_similarity(job_offer, job_alert):
    try:
        texts = [
            f"{job_offer.job_title} {job_offer.location} {job_offer.type} {job_offer.salary}",
            f"{job_alert.job_title} {job_alert.location} {job_alert.job_type} {job_alert.salary}"
        ]
        vectorizer = TfidfVectorizer().fit_transform(texts)
        vectors = vectorizer.toarray()
        cosine_sim = cosine_similarity(vectors)
        return cosine_sim[0, 1]
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return None


def find_and_notify_similar_jobs(threshold=0.5):
    job_alerts = JobAlert.query.filter_by(alertstatus=False).all()

    for job_alert in job_alerts:
        job_offers = Job_Offer_Post.query.filter(Job_Offer_Post.created_time > job_alert.created_time).all()

        for job_offer in job_offers:
            # Calculate the similarity between job alert and job offer
            similarity = get_cosine_similarity(job_offer, job_alert)
            if similarity is not None and similarity >= threshold:
                body = f"""
                Hi,

                A new job matching your alert has been posted:

                Job Title: {job_offer.job_title}
                Location: {job_offer.location}
                Type: {job_offer.type}
                Salary: {job_offer.salary}
                Description: {job_offer.description}

                Best,
                Your Job Portal
                """
                send_status = send_email(job_alert.user_email, 'New Job Alert', body)
                if send_status == 'Email sent successfully!':
                    # Update alert status only if it was False before
                    if job_alert.alertstatus == False:
                        job_alert.alertstatus = True
                        db.session.commit()

    return redirect('/profile')

       
        

@app.route('/submitFeedback',methods=['POST','GET'])
def submitFeedback():
    if request.method == 'POST': 
        feedback = request.form['feedback']
        email = session.get('user_email')
        user_id = session.get('user_id') 
        newfeedback = FeedBack(feedback=feedback,email=email,user_id=user_id)
        db.session.add(newfeedback)
        db.session.commit()
        return redirect('/profile')
    return render_template('feedback.html')

@app.route('/latest_job_offers', methods=['GET'])
def latest_job_offers():
    today = datetime.today().date()
    fifteen_days_ago = today - timedelta(days=7)
    
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Number of items per page
    
    job_offers = Job_Offer_Post.query.filter(Job_Offer_Post.created_date >= fifteen_days_ago).paginate(page=page, per_page=per_page)
    
    return render_template('latest_job_offers.html', job_offers=job_offers)

if JobAlert.query.first():
    find_and_notify_similar_jobs()
    

ITEMS_PER_PAGE = 3

def get_profile_and_job_posts():
    user_id = session.get('user_id')  # Assuming user_email is stored in session
    if not user_id:
        return None, []

    # Fetch the profile associated with the logged-in user's email
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        return None, []

    # Fetch all job posts (or apply any additional filters as necessary)
    job_posts = Job_Offer_Post.query.all()
    
    return profile, job_posts

def calculate_similarities(profile, job_posts):
    # Prepare the data
    profile_data = [profile.skills + ' ' + profile.title + ' ' + profile.address]
    job_posts_data = [job_post.skill_requirement + ' ' + job_post.job_title + ' ' + job_post.location for job_post in job_posts]

    # Combine data
    all_data = profile_data + job_posts_data

    # Vectorize
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(all_data)

    # Compute cosine similarity
    profile_vector = vectors[0]
    job_post_vectors = vectors[1:]

    similarities = cosine_similarity(profile_vector, job_post_vectors).flatten()
    
    return similarities

def filter_job_posts(job_posts, similarities, threshold=0.2):
    recommended_jobs = []
    for job_post, similarity in zip(job_posts, similarities):
        if similarity > threshold:
            recommended_jobs.append(job_post)
    return recommended_jobs

def paginate_jobs(jobs, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return jobs[start:end]

@app.route('/show_recommendations')
def show_recommendations():
    profile, job_posts = get_profile_and_job_posts()
    similarities = calculate_similarities(profile, job_posts)
    recommended_jobs = filter_job_posts(job_posts, similarities)
    
    # Get the page number from the query parameters (default is 1)
    page = int(request.args.get('page', 1))
    
    # Paginate the recommended jobs
    paginated_jobs = paginate_jobs(recommended_jobs, page)
    
    # Calculate the total number of pages
    total_pages = (len(recommended_jobs) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    return render_template('recommendation.html', jobs=paginated_jobs, page=page, total_pages=total_pages)


@app.route('/manage_users', methods=['GET'])
def manage_users():
    users = User.query.all()  # Fetch all users from the database
    return render_template('admin_users.html', users=users)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/view_user/<int:user_id>', methods=['GET'])
def view_user(user_id):
    user = User.query.get(user_id)
    return render_template('view_user.html', user=user)

@app.route('/manage_job_alerts', methods=['GET'])
def manage_job_alerts():
    job_alerts = JobAlert.query.all()  # Fetch all job alerts from the database
    return render_template('admin_job_alerts.html', job_alerts=job_alerts)

@app.route('/delete_job_alert/<int:job_alert_id>', methods=['POST'])
def delete_job_alert(job_alert_id):
    job_alert = JobAlert.query.get(job_alert_id)
    if job_alert:
        db.session.delete(job_alert)
        db.session.commit()
    return redirect(url_for('manage_job_alerts'))


@app.route('/manage_job_offer_posts', methods=['GET'])
def manage_job_offer_posts():
    current_month = datetime.now().month
    current_year = datetime.now().year
    job_posts = Job_Offer_Post.query.filter(
        db.extract('month', Job_Offer_Post.created_date) == current_month,
        db.extract('year', Job_Offer_Post.created_date) == current_year
    ).all()  # Fetch all job posts from the current month
    return render_template('admin_job_offer_posts.html', job_posts=job_posts)

@app.route('/delete_job_post/<int:post_id>', methods=['POST'])
def delete_job_post(post_id):
    job_post = Job_Offer_Post.query.get(post_id)
    if job_post:
        db.session.delete(job_post)
        db.session.commit()
    return redirect(url_for('manage_job_offer_posts'))


@app.route('/manage_reviews', methods=['GET'])
def manage_reviews():
    reviews = FeedBack.query.all()  # Fetch all reviews from the database
    return render_template('admin_reviews.html', reviews=reviews)

@app.route('/delete_review/<int:feedback_id>', methods=['POST'])
def delete_review(feedback_id):
    review = FeedBack.query.get(feedback_id)
    if review:
        db.session.delete(review)
        db.session.commit()
    return redirect(url_for('manage_reviews'))



if __name__== '__main__':
    app.run(debug=True)
 



