from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash
import requests
from ..decorators import role_required
from ..models import PasswordResetToken, User, Movie, Review
from ..forms import RegisterForm, LoginForm, MovieForm, ReviewForm, RequestResetForm, ResetPasswordForm
from ..extensions import db
import datetime

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.user_dashboard'))
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        email = form.email.data
        user = User(
            username=form.username.data,
            password=hashed_pw,
            email=email,
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if user.is_banned:
                flash("You are banned.", "danger")
                return redirect(url_for('main.login'))
            login_user(user)
            flash("Login successful!", "success")
            print(current_user.role)
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.role == 'moderator':
                return redirect(url_for('admin.moderator_dashboard'))
            else:
                return redirect(url_for('main.user_dashboard'))
        else:
            flash("Invalid email or password.", "danger")
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def user_dashboard():
    return render_template('user.html', user=current_user)

@main.route('/movies')
@login_required
def movies():
    sort = request.args.get('sort','rating_desc')
    genre_filter = request.args.get('genre', '')

    movies_query = Movie.query

    if genre_filter:
        movies_query = movies_query.filter(Movie.genre.ilike(f"%{genre_filter}%"))

    movies_list = movies_query.all()
    if sort == 'title_asc':
        movies_list.sort(key=lambda m: m.title.lower())
    elif sort == 'title_desc':
        movies_list.sort(key=lambda m: m.title.lower(), reverse=True)
    elif sort == 'rating_asc':
        movies_list.sort(key=lambda m: m.computed_rating)
    elif sort == 'rating_desc':
        movies_list.sort(key=lambda m: m.computed_rating, reverse=True)

    all_genres = []
    for m in Movie.query.all():
        if m.genre:
            all_genres.extend([g.strip() for g in m.genre.split(',')])
    genres = sorted(set(all_genres))

    return render_template(
        'movies.html',
        movies=movies_list,
        genres=genres,
        current_user=current_user
    )
@main.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    if current_user.id != review.user_id and current_user.role not in ['moderator', 'admin']:
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

@main.route('/add_movie', methods=['GET', 'POST'])
@login_required
@role_required('moderator', 'admin')
def add_movie():
    if current_user.role not in ('admin', 'moderator'):
        flash('Permission denied', 'danger')
        return redirect(url_for('main.index'))

    form = MovieForm()
    if form.validate_on_submit():
        title = form.title.data
        
        api_key = "9eb2235f"
        try:
            response = requests.get(
                f"http://www.omdbapi.com/?t={title}&apikey={api_key}",
                timeout=5
            )
            response.raise_for_status()
            movie_data = response.json()
        except requests.RequestException as e:
            flash(f"Error connecting to OMDb API: {e}", 'danger')
            return redirect(url_for('main.add_movie'))

        if movie_data.get('Response') == 'False':
            flash(f"Movie '{title}' not found in OMDb.", 'danger')
            return redirect(url_for('main.add_movie'))

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
        return redirect(url_for('main.index'))

    return render_template('add_movie.html', form=form)


@main.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('main.movie_details', movie_id=movie.id))
    sort = request.args.get('sort', 'newest')
    rating_filter = request.args.get('rating_filter', 'all')

    query = Review.query.filter_by(movie_id=movie_id)

    # Apply rating filter
    if rating_filter != 'all':
        query = query.filter(Review.rating >= int(rating_filter))

    # Apply sort order
    if sort == 'newest':
        query = query.order_by(Review.timestamp.desc())
    elif sort == 'oldest':
        query = query.order_by(Review.timestamp.asc())

    reviews = query.all()

    return render_template(
        'movie_details.html',
        movie=movie,
        reviews=reviews,
        sort=sort,
        rating_filter=rating_filter,
        form=form,
        avarage_rating=movie.computed_rating
    )






@main.route('/request_reset', methods=['GET', 'POST'])
def request_reset():
 form = RequestResetForm()
 if form.validate_on_submit():
  email = form.email.data
  user = User.query.filter_by(email=email).first()
  if user:
   token = PasswordResetToken.generate(user.id)
   reset_link = url_for('main.reset_password', token=token, _external=True)
   print(f"Reset link for {email}: {reset_link}")  
   flash("If this email exists, a reset link has been sent.", "info")
   return redirect(url_for('main.login'))
 return render_template('request_reset.html', form=form)

@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
 prt = PasswordResetToken.query.filter_by(token=token).first()
 if not prt or not prt.is_valid():
  flash("Invalid or expired token.", "danger")
  return redirect(url_for('main.login'))

 form = ResetPasswordForm()
 if form.validate_on_submit():
    user = User.query.get(prt.user_id)
    user.set_password(form.password.data)
    db.session.commit()

    prt.used = True
    db.session.commit()

    flash("Your password has been reset successfully!", "success")
    return redirect(url_for('main.login'))

 return render_template('reset_password.html', form=form)

@main.route('/admin')
@login_required
@role_required('admin')

def admin_dashboard():
    return render_template('admin.html')


@main.route('/moderator')
@login_required
@role_required('moderator', 'admin')

def moderator_dashboard():
    return render_template('manager.html')

@main.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
  
    if current_user.id == review.user_id or current_user.role in ['moderator', 'admin']:
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully!', 'success')
    else:
        flash('You do not have permission to delete this review.', 'danger')
    
    return redirect(request.referrer or url_for('index'))

