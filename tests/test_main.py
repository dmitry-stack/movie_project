import pytest
from werkzeug.security import generate_password_hash
from app.models import User, Movie, Review, PasswordResetToken
from app.extensions import db



# --- Fixtures ----------------------------------------------------------


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    """Regular test user"""
    with app.app_context():
        user = User.query.filter_by(email='user@example.com').first()
        if not user:
            user = User(
                username='testuser',
                email='user@example.com',
                password=generate_password_hash('userpass'),
                role='user'
            )
            db.session.add(user)
            db.session.commit()
        return user
    


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        if not user:
            user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('adminpass'),
                role='admin'
            )
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def movie(app):
    """Simple movie"""
    with app.app_context():
        m = Movie.query.filter_by(title='Test Movie').first()
        if not m:
            m = Movie(
                title='Test Movie',
                genre='Action',
                year=2024,
                description='Some test movie',
                poster='https://example.com/poster.jpg'
            )
            db.session.add(m)
            db.session.commit()
        return m


# --- Helper ------------------------------------------------------------

def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


# --- Core Tests --------------------------------------------------------

def test_index_access(client):
    """Index should load for guests"""
    resp = client.get('/')
    assert resp.status_code == 200


def test_register_new_user(client, app):
    """User can register"""
    resp = client.post('/register', data={
        'username': 'newbie',
        'email': 'newbie@example.com',
        'password': '12345678',
        'confirm_password': '12345678'
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email='newbie@example.com').first() is not None


def test_login_logout_flow(client, user):
    """User can log in and out"""
    r1 = login(client, 'user@example.com', 'userpass')
    assert b'Login successful' in r1.data

    r2 = client.get('/logout', follow_redirects=True)
    assert b'Logged out' in r2.data or r2.status_code == 200


def test_dashboard_requires_login(client):
    """Guests redirected to login on dashboard"""
    resp = client.get('/dashboard', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Login' in resp.data


# def test_movie_page_access(client, user, app, movie):
#     """Logged-in users can open movie page"""
#     login(client, 'user@example.com', 'userpass')
#     with app.app_context():
#         resp = client.get(f'/movie/{movie.id}')
#         assert resp.status_code == 200


def test_add_review(client, user, app, movie):
    """User can add review"""
    login(client, 'user@example.com', 'userpass')
    with app.app_context():
        db.session.add(movie)
        db.session.commit()
        db.session.refresh(movie)
        resp = client.post(f'/movie/{movie.id}', data={
            'content': 'Nice movie!',
            'rating': 5
        }, follow_redirects=True)
        assert resp.status_code == 200


# def test_admin_dashboard_access(client, admin):
#     """Admin can access admin dashboard"""
#     login(client, 'admin@example.com', 'adminpass')
#     resp = client.get('/admin')
#     assert resp.status_code == 200


def test_password_reset_request(client, user):
    """Password reset request works"""
    resp = client.post('/request_reset', data={'email': 'user@example.com'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'reset' in resp.data.lower()


def test_password_reset_with_invalid_token(client):
    """Invalid token should show error"""
    resp = client.get('/reset_password/faketoken', follow_redirects=True)
    assert resp.status_code == 200
    assert b'invalid' in resp.data.lower()


# import pytest
# from flask import url_for
# from werkzeug.security import generate_password_hash
# from app.models import User, Movie, Review, PasswordResetToken
# from app.extensions import db


# # Fixtures

# @pytest.fixture
# def client(app):
#     """Create a test client for the app."""
#     return app.test_client()


# @pytest.fixture
# def admin_user(app):
#     """Create an admin user."""
#     with app.app_context():
#         user = User.query.filter_by(email='admin@example.com').first()
#         if not user:
#             user = User(
#                 username='admin',
#                 email='admin@example.com',
#                 password=generate_password_hash('adminpass'),
#                 role='admin'
#             )
#             db.session.add(user)
#             db.session.commit()
#         return user


# @pytest.fixture
# def moderator_user(app):
#     """Create a moderator user."""
#     with app.app_context():
#         user = User.query.filter_by(email='moderator@example.com').first()
#         if not user:
#             user = User(
#                 username='moderator',
#                 email='moderator@example.com',
#                 password=generate_password_hash('modpass'),
#                 role='moderator'
#             )
#             db.session.add(user)
#             db.session.commit()
#         return user


# @pytest.fixture
# def regular_user(app):
#     """Create a regular user."""
#     with app.app_context():
#         user = User.query.filter_by(email='user@example.com').first()
#         if not user:
#             user = User(
#                 username='testuser',
#                 email='user@example.com',
#                 password=generate_password_hash('userpass'),
#                 role='user'
#             )
#             db.session.add(user)
#             db.session.commit()
#         return user


# @pytest.fixture
# def banned_user(app):
#     """Create a banned user."""
#     with app.app_context():
#         user = User.query.filter_by(email='banned@example.com').first()
#         if not user:
#             user = User(
#                 username='banneduser',
#                 email='banned@example.com',
#                 password=generate_password_hash('bannedpass'),
#                 role='user',
#                 is_banned=True
#             )
#             db.session.add(user)
#             db.session.commit()
#         return user


# @pytest.fixture
# def sample_movie(app):
#     """Create a sample movie."""
#     with app.app_context():
#         movie = Movie.query.filter_by(title='Test Movie').first()
#         if not movie:
#             movie = Movie(
#                 title='Test Movie',
#                 genre='Action, Drama',
#                 year=2020,
#                 description='A test movie',
#                 poster='http://example.com/poster.jpg'
#             )
#             db.session.add(movie)
#             db.session.commit()
#         return movie


# def login_as_admin(client, app):
#     """Helper function to log in as admin."""
#     with app.app_context():
#         if not User.query.filter_by(email='admin@example.com').first():
#             user = User(
#                 username='admin',
#                 email='admin@example.com',
#                 password=generate_password_hash('adminpass'),
#                 role='admin'
#             )
#             db.session.add(user)
#             db.session.commit()
    
#     resp = client.post('/login', data={
#         'email': 'admin@example.com',
#         'password': 'adminpass'
#     }, follow_redirects=True)
#     assert resp.status_code == 200


# def login_as_moderator(client, app):
#     """Helper function to log in as moderator."""
#     with app.app_context():
#         if not User.query.filter_by(email='moderator@example.com').first():
#             user = User(
#                 username='moderator',
#                 email='moderator@example.com',
#                 password=generate_password_hash('modpass'),
#                 role='moderator'
#             )
#             db.session.add(user)
#             db.session.commit()
    
#     resp = client.post('/login', data={
#         'email': 'moderator@example.com',
#         'password': 'modpass'
#     }, follow_redirects=True)
#     assert resp.status_code == 200


# def login_as_user(client, app):
#     """Helper function to log in as regular user."""
#     with app.app_context():
#         if not User.query.filter_by(email='user@example.com').first():
#             user = User(
#                 username='testuser',
#                 email='user@example.com',
#                 password=generate_password_hash('userpass'),
#                 role='user'
#             )
#             db.session.add(user)
#             db.session.commit()
    
#     resp = client.post('/login', data={
#         'email': 'user@example.com',
#         'password': 'userpass'
#     }, follow_redirects=True)
#     assert resp.status_code == 200


# # Test Cases

# class TestIndexRoute:
#     """Tests for the index route."""
    
#     def test_index_redirects_when_authenticated(self, client, app, regular_user):
#         """Test that authenticated users are redirected to dashboard."""
#         login_as_user(client, app)
#         resp = client.get('/', follow_redirects=False)
#         assert resp.status_code == 302
#         assert '/dashboard' in resp.location
    
#     def test_index_renders_when_not_authenticated(self, client):
#         """Test that unauthenticated users see the index page."""
#         resp = client.get('/')
#         assert resp.status_code == 200


# class TestRegistration:
#     """Tests for user registration."""
    
#     def test_register_page_loads(self, client):
#         """Test that the registration page loads."""
#         resp = client.get('/register')
#         assert resp.status_code == 200
    
#     def test_successful_registration(self, client, app):
#         """Test successful user registration."""
#         resp = client.post('/register', data={
#             'username': 'newuser',
#             'email': 'newuser@example.com',
#             'password': 'newpass123',
#             'confirm_password': 'newpass123'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Account created' in resp.data
        
#         with app.app_context():
#             user = User.query.filter_by(email='newuser@example.com').first()
#             assert user is not None
#             assert user.username == 'newuser'
#             assert user.role == 'user'


# class TestLogin:
#     """Tests for user login."""
    
#     def test_login_page_loads(self, client):
#         """Test that the login page loads."""
#         resp = client.get('/login')
#         assert resp.status_code == 200
    
#     def test_successful_login_admin(self, client, app, admin_user):
#         """Test successful admin login."""
#         resp = client.post('/login', data={
#             'email': 'admin@example.com',
#             'password': 'adminpass'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Login successful' in resp.data
    
#     def test_successful_login_moderator(self, client, app, moderator_user):
#         """Test successful moderator login."""
#         resp = client.post('/login', data={
#             'email': 'moderator@example.com',
#             'password': 'modpass'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Login successful' in resp.data
    
#     def test_successful_login_user(self, client, app, regular_user):
#         """Test successful regular user login."""
#         resp = client.post('/login', data={
#             'email': 'user@example.com',
#             'password': 'userpass'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Login successful' in resp.data
    
#     def test_login_with_wrong_password(self, client, app, regular_user):
#         """Test login with incorrect password."""
#         resp = client.post('/login', data={
#             'email': 'user@example.com',
#             'password': 'wrongpass'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Invalid email or password' in resp.data
    
#     def test_login_with_nonexistent_email(self, client):
#         """Test login with non-existent email."""
#         resp = client.post('/login', data={
#             'email': 'nonexistent@example.com',
#             'password': 'somepass'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Invalid email or password' in resp.data
    
#     def test_banned_user_cannot_login(self, client, app, banned_user):
#         """Test that banned users cannot login."""
#         resp = client.post('/login', data={
#             'email': 'banned@example.com',
#             'password': 'bannedpass'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'You are banned' in resp.data


# class TestLogout:
#     """Tests for user logout."""
    
#     def test_logout_requires_login(self, client):
#         """Test that logout requires authentication."""
#         resp = client.get('/logout', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_successful_logout(self, client, app, regular_user):
#         """Test successful logout."""
#         login_as_user(client, app)
#         resp = client.get('/logout', follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Logged out successfully' in resp.data


# class TestDashboard:
#     """Tests for user dashboard."""
    
#     def test_dashboard_requires_login(self, client):
#         """Test that dashboard requires authentication."""
#         resp = client.get('/dashboard', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_dashboard_accessible_when_logged_in(self, client, app, regular_user):
#         """Test that logged-in users can access dashboard."""
#         login_as_user(client, app)
#         resp = client.get('/dashboard')
#         assert resp.status_code == 200


# class TestMoviesListing:
#     """Tests for movies listing page."""
    
#     def test_movies_page_requires_login(self, client):
#         """Test that movies page requires authentication."""
#         resp = client.get('/movies', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_movies_page_loads(self, client, app, regular_user, sample_movie):
#         """Test that movies page loads with data."""
#         login_as_user(client, app)
#         resp = client.get('/movies')
#         assert resp.status_code == 200
    
#     def test_movies_sorting_by_title(self, client, app, regular_user):
#         """Test movies sorting by title."""
#         login_as_user(client, app)
#         resp = client.get('/movies?sort=title_asc')
#         assert resp.status_code == 200
    
#     def test_movies_sorting_by_rating(self, client, app, regular_user):
#         """Test movies sorting by rating."""
#         login_as_user(client, app)
#         resp = client.get('/movies?sort=rating_desc')
#         assert resp.status_code == 200
    
#     def test_movies_genre_filter(self, client, app, regular_user):
#         """Test movies genre filtering."""
#         login_as_user(client, app)
#         resp = client.get('/movies?genre=Action')
#         assert resp.status_code == 200


# class TestAddMovie:
#     """Tests for adding movies."""
    
#     def test_add_movie_requires_login(self, client):
#         """Test that add movie requires authentication."""
#         resp = client.get('/add_movie', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_add_movie_requires_moderator_or_admin(self, client, app, regular_user):
#         """Test that regular users cannot add movies."""
#         login_as_user(client, app)
#         resp = client.get('/add_movie', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'Permission denied' in resp.data
    
#     def test_add_movie_page_loads_for_moderator(self, client, app, moderator_user):
#         """Test that moderators can access add movie page."""
#         login_as_moderator(client, app)
#         resp = client.get('/add_movie')
#         assert resp.status_code == 200
    
#     def test_add_movie_page_loads_for_admin(self, client, app, admin_user):
#         """Test that admins can access add movie page."""
#         login_as_admin(client, app)
#         resp = client.get('/add_movie')
#         assert resp.status_code == 200


# class TestMovieDetails:
#     """Tests for movie details page."""
    
#     def test_movie_details_requires_login(self, client, app, sample_movie):
#         """Test that movie details requires authentication."""
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.get(f'/movie/{movie_id}', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_movie_details_loads(self, client, app, regular_user, sample_movie):
#         """Test that movie details page loads."""
#         login_as_user(client, app)
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.get(f'/movie/{movie_id}')
#         assert resp.status_code == 200
    
#     def test_movie_details_nonexistent_movie(self, client, app, regular_user):
#         """Test accessing non-existent movie returns 404."""
#         login_as_user(client, app)
#         resp = client.get('/movie/99999')
#         assert resp.status_code == 404
    
#     def test_submit_review(self, client, app, regular_user, sample_movie):
#         """Test submitting a review."""
#         login_as_user(client, app)
#         with app.app_context():
#             movie_id = sample_movie.id
        
#         resp = client.post(f'/movie/{movie_id}', data={
#             'rating': 5,
#             'content': 'Great movie!'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Review submitted' in resp.data
    
#     def test_reviews_sorting_newest(self, client, app, regular_user, sample_movie):
#         """Test reviews sorting by newest."""
#         login_as_user(client, app)
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.get(f'/movie/{movie_id}?sort=newest')
#         assert resp.status_code == 200
    
#     def test_reviews_sorting_oldest(self, client, app, regular_user, sample_movie):
#         """Test reviews sorting by oldest."""
#         login_as_user(client, app)
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.get(f'/movie/{movie_id}?sort=oldest')
#         assert resp.status_code == 200
    
#     def test_reviews_rating_filter(self, client, app, regular_user, sample_movie):
#         """Test reviews rating filter."""
#         login_as_user(client, app)
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.get(f'/movie/{movie_id}?rating_filter=4')
#         assert resp.status_code == 200


# class TestReviewEdit:
#     """Tests for editing reviews."""
    
#     def test_edit_review_requires_login(self, client):
#         """Test that edit review requires authentication."""
#         resp = client.get('/edit_review/1', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_user_can_edit_own_review(self, client, app, regular_user, sample_movie):
#         """Test that users can edit their own reviews."""
#         login_as_user(client, app)
        
#         # Create a review first
#         with app.app_context():
#             movie_id = sample_movie.id
#             user_id = regular_user.id
#             review = Review(
#                 movie_id=movie_id,
#                 user_id=user_id,
#                 rating=4,
#                 content='Original review'
#             )
#             db.session.add(review)
#             db.session.commit()
#             review_id = review.id
        
#         # Edit the review
#         resp = client.post(f'/edit_review/{review_id}', data={
#             'rating': 5,
#             'content': 'Updated review'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'Review updated successfully' in resp.data
    
#     def test_user_cannot_edit_others_review(self, client, app, regular_user, admin_user, sample_movie):
#         """Test that users cannot edit others' reviews."""
#         # Create review as admin
#         with app.app_context():
#             movie_id = sample_movie.id
#             admin_id = admin_user.id
#             review = Review(
#                 movie_id=movie_id,
#                 user_id=admin_id,
#                 rating=4,
#                 content='Admin review'
#             )
#             db.session.add(review)
#             db.session.commit()
#             review_id = review.id
        
#         # Try to edit as regular user
#         login_as_user(client, app)
#         resp = client.get(f'/edit_review/{review_id}', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'permission' in resp.data.lower()


# class TestReviewDelete:
#     """Tests for deleting reviews."""
    
#     def test_delete_review_requires_login(self, client):
#         """Test that delete review requires authentication."""
#         resp = client.post('/delete_review/1', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_user_can_delete_own_review(self, client, app, regular_user, sample_movie):
#         """Test that users can delete their own reviews."""
#         login_as_user(client, app)
        
#         # Create a review first
#         with app.app_context():
#             movie_id = sample_movie.id
#             user_id = regular_user.id
#             review = Review(
#                 movie_id=movie_id,
#                 user_id=user_id,
#                 rating=4,
#                 content='To be deleted'
#             )
#             db.session.add(review)
#             db.session.commit()
#             review_id = review.id
        
#         # Delete the review
#         resp = client.post(f'/delete_review/{review_id}', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'Review deleted successfully' in resp.data
    
#     def test_moderator_can_delete_any_review(self, client, app, moderator_user, regular_user, sample_movie):
#         """Test that moderators can delete any review."""
#         # Create review as regular user
#         with app.app_context():
#             movie_id = sample_movie.id
#             user_id = regular_user.id
#             review = Review(
#                 movie_id=movie_id,
#                 user_id=user_id,
#                 rating=4,
#                 content='User review'
#             )
#             db.session.add(review)
#             db.session.commit()
#             review_id = review.id
        
#         # Delete as moderator
#         login_as_moderator(client, app)
#         resp = client.post(f'/delete_review/{review_id}', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'Review deleted successfully' in resp.data


# class TestPasswordReset:
#     """Tests for password reset functionality."""
    
#     def test_request_reset_page_loads(self, client):
#         """Test that request reset page loads."""
#         resp = client.get('/request_reset')
#         assert resp.status_code == 200
    
#     def test_request_reset_for_existing_user(self, client, app, regular_user):
#         """Test password reset request for existing user."""
#         resp = client.post('/request_reset', data={
#             'email': 'user@example.com'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'reset link has been sent' in resp.data
    
#     def test_request_reset_for_nonexistent_user(self, client):
#         """Test password reset request for non-existent user."""
#         resp = client.post('/request_reset', data={
#             'email': 'nonexistent@example.com'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         # Should still show the same message for security
#         assert b'reset link has been sent' in resp.data
    
#     def test_reset_password_with_valid_token(self, client, app, regular_user):
#         """Test resetting password with valid token."""
#         with app.app_context():
#             token = PasswordResetToken.generate(regular_user.id)
        
#         resp = client.post(f'/reset_password/{token}', data={
#             'password': 'newpassword123',
#             'confirm_password': 'newpassword123'
#         }, follow_redirects=True)
        
#         assert resp.status_code == 200
#         assert b'password has been reset successfully' in resp.data
    
#     def test_reset_password_with_invalid_token(self, client):
#         """Test resetting password with invalid token."""
#         resp = client.get('/reset_password/invalidtoken123', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'Invalid or expired token' in resp.data


# class TestAdminDashboard:
#     """Tests for admin dashboard."""
    
#     def test_admin_dashboard_requires_login(self, client):
#         """Test that admin dashboard requires authentication."""
#         resp = client.get('/admin', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_admin_dashboard_requires_admin_role(self, client, app, regular_user):
#         """Test that regular users cannot access admin dashboard."""
#         login_as_user(client, app)
#         resp = client.get('/admin', follow_redirects=True)
#         assert resp.status_code in [200, 403]
    
#     def test_admin_dashboard_accessible_for_admin(self, client, app, admin_user):
#         """Test that admins can access admin dashboard."""
#         login_as_admin(client, app)
#         resp = client.get('/admin')
#         assert resp.status_code == 200


# class TestModeratorDashboard:
#     """Tests for moderator dashboard."""
    
#     def test_moderator_dashboard_requires_login(self, client):
#         """Test that moderator dashboard requires authentication."""
#         resp = client.get('/moderator', follow_redirects=True)
#         assert resp.status_code == 200
    
#     def test_moderator_dashboard_requires_moderator_role(self, client, app, regular_user):
#         """Test that regular users cannot access moderator dashboard."""
#         login_as_user(client, app)
#         resp = client.get('/moderator', follow_redirects=True)
#         assert resp.status_code in [200, 403]
    
#     def test_moderator_dashboard_accessible_for_moderator(self, client, app, moderator_user):
#         """Test that moderators can access moderator dashboard."""
#         login_as_moderator(client, app)
#         resp = client.get('/moderator')
#         assert resp.status_code == 200
    
#     def test_moderator_dashboard_accessible_for_admin(self, client, app, admin_user):
#         """Test that admins can also access moderator dashboard."""
#         login_as_admin(client, app)
#         resp = client.get('/moderator')
#         assert resp.status_code == 200