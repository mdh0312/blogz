from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:foobar@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'bf6b6727c5edc7bd53dd9903e769d243'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(2000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, user):
        self.title = title
        self.body = body
        self.user = user

class User(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(60)) #shouldn't this be set to UNIQUE?
    password = db.Column(db.String(40))
    user_posts = db.relationship('Blog', backref = 'user')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.route('/', methods = ['POST', 'GET'])
def index():

    if request.args.get('user'):
        user_id = request.args.get('user')
        user = User.query.get(int(user_id))
        posts = Blog.query.filter_by(user_id = user_id).all()
        return render_template('user.html', user = user, posts = posts, 
        title = 'Blogz')
    
    users = User.query.all()
    return render_template('index.html', users = users, title = 'Blogz')

@app.route('/blog/newpost', methods = ['POST', 'GET'])
def new_post():
    if request.method ==  'POST':
        owner = User.query.filter_by(username = session['username']).first()
        title = request.form['post_title']
        body = request.form['post_body']
		
        title_error = ""
        body_error = ""

        if title ==  "":
            title_error = "Please enter the title"
        if body ==  "":
            body_error = "Please type something to post"

        if (title ==  "") or (body ==  ""):
            return render_template('newpost.html', title_error = title_error, 
            body_error = body_error, post_title = title, body = body)
        else:
            new_post = Blog(title, body, owner)
            db.session.add(new_post)
            db.session.commit()
            posts = Blog.query.all()
            post = posts[len(posts) - 1]
            return render_template('post.html', post = post)

    return render_template('newpost.html', title = 'Blogz')

@app.route('/blog', methods = ['POST', 'GET'])
def blog():

    if request.args.get('id'):
        post_id = request.args.get('id')
        post = Blog.query.get(int(post_id))
        return render_template('post.html', post = post, title = 'Blogz')
    
    posts = Blog.query.all()
    return render_template('blog.html', posts = posts, title = "Blogz")

@app.route('/blog/signup', methods = ['POST', 'GET'])        
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        existing_user = User.query.filter_by(username = username).first()
        
        user_error = ""
        username_error = ""
        password_error = ""
        verify_error = ""
        
        if existing_user:
            user_error = "Username already exists"
            username = ""
            password = ""
            verify = ""
            return render_template('signup.html', username = username, 
            username_error = user_error, password = password, 
            password_error = password_error, verify_error = verify_error, 
            verify = verify, title = 'Sign Up')
          
        elif (not (3 <= len(username) <= 20)) or (" " in username):
            username_error = "Username must be between 3 and 20 characters, inclusive and not contain blanks"
            username = ""
            password = ""
            verify = ""
            return render_template('signup.html', username = username, 
            username_error = username_error, password = password, 
            password_error = password_error, verify_error = verify_error, 
            verify = verify, title = 'Sign Up')
          
        elif (not (3 <= len(password) <= 20)) or (" " in password):
            password_error = "Password must be between 3 and 20 characters, inclusive and not contain blanks"
            password = ""
            verify = ""
            return render_template('signup.html', username = username, 
            username_error = user_error, password = password, 
            password_error = password_error, verify_error = verify_error, 
            verify = verify, title = 'Sign Up')

        elif verify != password:
            verify_error = "Verify Password does not match Password"
            password = ""
            verify = ""
            return render_template('signup.html', username = username, 
            username_error = user_error, password = password, 
            password_error = password_error, verify_error = verify_error, 
            verify = verify, title = 'Sign Up')
            
        elif ((username_error == "") and (password_error == "") 
        and (verify_error == "") and (user_error == "")):
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/blog/newpost')
            
        elif user_error != "":
            return render_template('signup.html', username = username, 
            username_error = user_error, password = password, 
            password_error = password_error, verify_error = verify_error, 
            verify = verify, title = 'Sign Up')
        else:           
            return render_template('signup.html', username = username, 
            username_error = username_error, password = password, 
            password_error = password_error, verify_error = verify_error, 
            verify = verify, title = 'Sign Up')  

    return render_template('signup.html', title = 'Sign Up')

@app.before_request
def require_login():
    allowed_routes = ['index', 'blog', 'signup', 'login']
    if (request.endpoint not in allowed_routes) and ('username' not in session):
        return redirect('/blog/login')

@app.route('/blog/login', methods = ['POST', 'GET'])
def login():
    if request.method ==  'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()
                
        username_error = ""
        password_error = ""
        
        if not user:
            username_error = "Username does not exist"
            return render_template('login.html', username_error = username_error, 
            password_error = password_error)
        else:
            if user.password == password:
                session['username'] = username
                return redirect('/blog/newpost')
            else:
                password_error = "Incorrect password"
                return render_template('login.html', username_error = username_error, 
                password_error = password_error)

    return render_template('login.html')

@app.route('/blog/logout')
def logout():
    del session['username']
    return redirect('/blog')

if __name__ ==  '__main__':
    app.run()