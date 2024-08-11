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


class User(db.Model):
    use_id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(20), nullable=False,unique=False)
    email = db.Column(db.String(100), nullable=False,unique=True)
    password = db.Column(db.String(100), nullable=False)

class Job_Offer_Post(db.Model):
    post_id = db.Column(db.Integer(),primary_key=True)
    username = db.Column(db.String(100),nullable=False)
    job_title = db.Column(db.String(100),nullable=False)
    age = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100),nullable=False)
    salary = db.Column(db.String(200), nullable=False)
    created_time = db.Column(db.DateTime,default=datetime.utcnow)
    created_date = db.Column(db.Date,default=date.today)
    deadline = db.Column(db.String(100), nullable=False)
    location =db.Column(db.String(100), nullable=False)
    description =db.Column(db.String,nullable=False)
    skill_requirement = db.Column(db.Text, nullable=False) 
    phone = db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(50),nullable=False)
    type = db.Column(db.String(100),nullable=False)
    edited = db.Column(db.Boolean,nullable=True, default=False)
    
class Admin(db.Model):
    admin_id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100),nullable=False)
    
class Profile(db.Model):
    user_profile_id = db.Column(db.Integer(),primary_key=True)
    name =db.Column(db.String(100),nullable=False)
    title = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer(),nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.String, nullable=False)
    experiences = db.Column(db.String, nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(100),nullable=False)
    address = db.Column(db.String, nullable=False)
    

class JobAlert(db.Model):
    job_alert_id = db.Column(db.Integer(), primary_key=True)
    job_title = db.Column(db.String(100),nullable=False)
    location = db.Column(db.String(100),nullable=False)
    job_type= db.Column(db.String(100),nullable=False)
    salary = db.Column(db.String(100),nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    alertstatus = db.Column(db.Boolean, default=False, nullable=True)
    created_date = db.Column(db.Date,default=date.today)
    created_time = db.Column(db.DateTime,default=datetime.utcnow)
    

    
class FeedBack(db.Model):
    feedback_id = db.Column(db.Integer(), primary_key = True)
    email = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    
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

@app.route('/profile',methods=['GET'])
def profile():
    if not session.get('user_logged_in'):
        return redirect('/login')
    user_email = session.get('user_email')
    user_alerts = JobAlert.query.filter_by(user_email=user_email).all()
    
    return render_template('profile.html', alerts=user_alerts)

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html', tilte='Register')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'winwinhtet' and password == 'pw123':
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                session['username'] = user.username
                session['user_logged_in'] = True
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

@app.route('/submitPost',methods=['GET','POST'])
def submitPost():
    if request.method == 'POST':
        job_title = request.form['title']
        username = session.get('username')
        email = request.form['email']
        age = request.form['age']
        salary= request.form['salary']
        gender = request.form['gender']
        deadline = request.form['deadline']     
        address = request.form['address']
        description = request.form['description']
        phone = request.form['contact']
        skills = request.form['skills']
        type = request.form['job_type']
        new_post = Job_Offer_Post(job_title=job_title, email=email,age=age,gender=gender,
                                  deadline=deadline,location=address,description=description,type=type,
                                  phone=phone,username=username,salary=salary,skill_requirement=skills)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/profile')
    return render_template('jobOffer.html')

# Association table for many-to-many relationship
job_alert_job_offer_association = db.Table('job_alert_job_offer',
    db.Column('job_alert_id', db.Integer, db.ForeignKey('job_alert.job_alert_id')),
    db.Column('post_id', db.Integer, db.ForeignKey('job_offer_post.post_id'))
)



@app.route('/submitJobAlert',methods=['GET','POST'])
def submitJobAlert():
    if request.method == 'POST':
        job_title = request.form['job_title']
        address = request.form['location']
        type = request.form['job_type']
        user_email = session.get('user_email')
        salary = request.form['salary']
        job_alert = JobAlert(job_title=job_title, location=address, job_type=type,user_email=user_email,salary = salary)
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

   

    
@app.route('/setprofile', methods=['GET'])
def setprofile():
    return render_template('setupprofile.html')

@app.route('/setupprofile', methods=['POST', 'GET'])
def setupprofile():
    if request.method == 'POST':
        print('post is okayy')
        full_name = request.form['fullName']
        phone_number = request.form['phoneNumber']
        email = request.form['email']
        address = request.form['address']
        age = request.form['age']
        gender = request.form['gender']
        job_title = request.form['jobTitle']
        skills = request.form['skills']
        experiences = request.form['experiences']

        new_profile = Profile(
            name=full_name,
            title=job_title,
            age=int(age),  # Convert age to integer
            gender=gender,
            skills=skills,
            experiences=experiences,
            contact=phone_number,
            contact_email=email,
            address=address
        )

        db.session.add(new_profile)
        db.session.commit()
        return redirect(url_for('profile'))
    return 'Method not allowed', 405
        
        

@app.route('/submitFeedback',methods=['POST','GET'])
def submitFeedback():
    if request.method == 'POST': 
        feedback = request.form['feedback']
        email = session.get('user_email')
        newfeedback = FeedBack(feedback=feedback,email=email)
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

if __name__== '__main__':
    app.run(debug=True)
 



