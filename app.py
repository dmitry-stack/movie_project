from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from forms import RegisterForm, LoginForm, MovieForm, ReviewForm

app = Flask(__name__,template_folder='templates')
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)  
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ======== MODELS =========
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('reviews', lazy=True))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ======== ROUTES =========
@app.route('/add_movie', methods=['GET', 'POST'])
@login_required
@role_required('manager', 'admin')
def add_movie():
    form = MovieForm()
    if form.validate_on_submit():
        movie = Movie(
            title=form.title.data,
            genre=form.genre.data,
            year=form.year.data,
            description=form.description.data
        )
        db.session.add(movie)
        db.session.commit()
        flash('Movie added successfully!', 'success')
        return redirect(url_for('movies'))
    return render_template('add_movie.html', form=form)

@app.route('/movies')
@login_required
def movies():
    genre_filter = request.args.get('genre')
    if genre_filter:
        movies_list = Movie.query.filter_by(genre=genre_filter).all()
    else:
        movies_list = Movie.query.all()
    genres = sorted(set([m.genre for m in Movie.query.all()]))
    return render_template('movies.html', movies=movies_list, genres=genres)


@app.route('/test')
def test():
    return render_template('test.html', name='World')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pw, role='user')
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
   form = LoginForm()
   if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')

           
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'manager':
                return redirect(url_for('manager_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

   return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
  
    if current_user.id == review.user_id or current_user.role in ['manager', 'admin']:
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully!', 'success')
    else:
        flash('You do not have permission to delete this review.', 'danger')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def movie_details(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    form = ReviewForm()

    if form.validate_on_submit():
        review = Review(
            movie_id=movie.id,
            user_id=current_user.id,
            #rating=form.rating.data,
            content=form.content.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('movie_details', movie_id=movie.id))
    else:
      print(form.errors) 
    sort = request.args.get('sort', 'newest')
    if sort == 'oldest':
        reviews = Review.query.filter_by(movie_id=movie.id).order_by(Review.timestamp.asc()).all()
    else:
        reviews = Review.query.filter_by(movie_id=movie.id).order_by(Review.timestamp.desc()).all()
    return render_template('movie_details.html', movie=movie,reviews=reviews, form=form, sort=sort)

@app.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    if current_user.id != review.user_id and current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to edit this review.', 'danger')
        return redirect(request.referrer or url_for('index'))

    form = ReviewForm(obj=review)
    if form.validate_on_submit():
        review.content = form.content.data
        db.session.commit()
        flash('Review updated successfully!', 'success')
        return redirect(request.referrer or url_for('index'))
    else:
        print(form.errors)
    
    return render_template('edit_review.html', form=form, review=review)

@app.route('/admin')
@login_required
@role_required('admin')

def admin_dashboard():
    return render_template('admin.html')


@app.route('/manager')
@login_required
@role_required('manager', 'admin')

def manager_dashboard():
    return render_template('manager.html')


@app.route('/user')
@login_required
@role_required('user', 'manager', 'admin')

def user_dashboard():
    return render_template('user.html')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
