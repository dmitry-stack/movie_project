from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
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
    is_banned = db.Column(db.Boolean, default=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    poster = db.Column(db.String(300), nullable=True)

    @property
    def average_rating(self):
        if not self.reviews or len(self.reviews) == 0:
            return 0
        return sum([r.rating for r in self.reviews]) / len(self.reviews)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, nullable=False, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('reviews', lazy=True))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def check_user_ban_status():
    if current_user.is_authenticated and current_user.is_banned:
        logout_user()
        flash("Ваш аккаунт был заблокирован.", "danger")
        return redirect(url_for('login'))
    
# ======== ROUTES =========
@app.route('/add_movie', methods=['GET', 'POST'])
@login_required
@role_required('manager', 'admin')
def add_movie():
    """
    Route for adding a new movie.
    Expected form fields in 'add_movie.html':
        - title: str, required, the title of the movie to add.
    """
    if current_user.role not in ('admin', 'manager'):
        flash('Permission denied', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        api_key = "9eb2235f"  

        
        try:
            response = requests.get(f"http://www.omdbapi.com/?t={title}&apikey={api_key}", timeout=5)
            response.raise_for_status()
            movie_data = response.json()
        except requests.RequestException as e:
            flash(f"Error connecting to OMDb API: {e}", 'danger')
            return redirect(url_for('add_movie'))

        if movie_data.get('Response') == 'False':
            flash(f"Movie '{title}' not found in OMDb.", 'danger')
            return redirect(url_for('add_movie'))

        movie = Movie(
            poster=movie_data.get('Poster'),
            title=movie_data.get('Title', title),
            genre=movie_data.get('Genre', 'Unknown'),
            year=int(movie_data.get('Year', 0)),
            description=movie_data.get('Plot', 'No description available.')
        )
        db.session.add(movie)
        db.session.commit()

        flash(f"Movie '{movie.title}' added successfully!", 'success')
        return redirect(url_for('index'))

    return render_template('add_movie.html')

@app.route('/api/search_movies')
@login_required
@role_required('manager', 'admin')
def api_search_movies():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Пустой запрос'}), 400

    api_key = "9eb2235f"
    url = f"https://www.omdbapi.com/?apikey={api_key}&s={query}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return jsonify({'error': f'Ошибка подключения к OMDb API: {e}'}), 500

    if data.get("Response") == "False" and "Too many results" in data.get("Error", ""):
    
     response2 = requests.get(f"https://www.omdbapi.com/?apikey={api_key}&t={query}", timeout=5)
     data2 = response2.json()
     if data2.get("Response") == "True":
        return jsonify([{
            "title": data2["Title"],
            "year": data2["Year"],
            "imdb_id": data2["imdbID"],
            "poster": data2["Poster"]
        }])
     else:
        return jsonify({'error': "Слишком много совпадений. Попробуйте уточнить название."}), 400

    results = []
    for movie in data.get("Search", [])[:5]:
        results.append({
            "title": movie["Title"],
            "year": movie["Year"],
            "imdb_id": movie["imdbID"],
            "poster": movie["Poster"]
        })

    return jsonify(results)

@app.route('/api/add_movie', methods=['POST'])
@login_required
@role_required('manager', 'admin')
def api_add_movie():
    data = request.get_json()
    imdb_id = data.get('imdb_id')
    api_key = "9eb2235f"

    if not imdb_id:
        return jsonify({'error': 'Не указан imdb_id'}), 400

    try:
        response = requests.get(f"https://www.omdbapi.com/?i={imdb_id}&apikey={api_key}", timeout=5)
        response.raise_for_status()
        movie_data = response.json()
    except requests.RequestException as e:
        return jsonify({'error': f'Ошибка подключения к OMDb API: {e}'}), 500

    if movie_data.get('Response') == 'False':
        return jsonify({'error': f"Фильм с ID {imdb_id} не найден."}), 404

    # Проверяем, нет ли уже такого фильма
    existing = Movie.query.filter_by(title=movie_data.get('Title')).first()
    if existing:
        return jsonify({'error': 'Такой фильм уже есть в базе.'}), 400

    movie = Movie(
        poster=movie_data.get('Poster'),
        title=movie_data.get('Title'),
        genre=movie_data.get('Genre', 'Unknown'),
        year=int(movie_data.get('Year', 0)),
        description=movie_data.get('Plot', 'No description available.')
    )
    db.session.add(movie)
    db.session.commit()

    return jsonify({'success': True, 'title': movie.title})

@app.route('/admin/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('manage_users.html', users=users)


@app.route('/admin/ban/<int:user_id>')
@login_required
def ban_user(user_id):
    if current_user.role != 'admin':
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Нельзя забанить другого администратора!", "warning")
        return redirect(url_for('manage_users'))

    user.is_banned = True
    db.session.commit()
    flash(f"Пользователь {user.username} забанен.", "danger")
    return redirect(url_for('manage_users'))


@app.route('/admin/unban/<int:user_id>')
@login_required
def unban_user(user_id):
    if current_user.role != 'admin':
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash(f"Пользователь {user.username} разблокирован.", "success")
    return redirect(url_for('manage_users'))

@app.route('/movies')
@login_required
def movies():
    genre_filter = request.args.get('genre')
    if genre_filter:
        movies_list = Movie.query.filter_by(genre=genre_filter).all()
    else:
        movies_list = Movie.query.all()
    genres = sorted(set([m.genre for m in Movie.query.all()]))
    ratings = sorted(set([m.average_rating for m in Movie.query.all()]))
    return render_template('movies.html', movies=movies_list, genres=genres, ratings=ratings,current_user=current_user)

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q', '')
    movies = []

    if query:
        movies = Movie.query.filter(Movie.title.ilike(f"%{query}%")).all()

    return render_template('search.html', movies=movies, query=query)

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
            if user.is_banned:
                flash("You are in the ban list", "danger")
                return redirect(url_for('login'))
           
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
            rating=form.rating.data,
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
    return render_template('movie_details.html', movie=movie, reviews=reviews, form=form, sort=sort, average_rating=movie.average_rating)

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
        review.rating = form.rating.data
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
