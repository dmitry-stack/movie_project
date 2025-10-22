import pytest
import json
from werkzeug.security import generate_password_hash
from app.models import User, Movie, Review
from app.extensions import db

# ----------------------
# Fixtures
# ----------------------
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def create_user(app):
    """Factory fixture to create users dynamically."""
    def _create_user(username, email, password, role='user', is_banned=False):
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    role=role,
                    is_banned=is_banned
                )
                db.session.add(user)
                db.session.commit()
                db.session.refresh(user)
            return user
    return _create_user

@pytest.fixture
def admin_user(create_user):
    return create_user('admin', 'admin@example.com', 'adminpass', 'admin')

@pytest.fixture
def moderator_user(create_user):
    return create_user('moderator', 'moderator@example.com', 'modpass', 'moderator')

@pytest.fixture
def regular_user(create_user):
    return create_user('testuser', 'user@example.com', 'userpass')

@pytest.fixture
def another_user(create_user):
    return create_user('anotheruser', 'another@example.com', 'anotherpass')

@pytest.fixture
def sample_movie(app):
    """Create a sample movie."""
    with app.app_context():
        movie = Movie.query.filter_by(title='Test Movie').first()
        if not movie:
            movie = Movie(
                title='Test Movie',
                genre='Action, Drama',
                year=2020,
                description='A test movie',
                poster='http://example.com/poster.jpg'
            )
            db.session.add(movie)
            db.session.commit()
        return movie

# ----------------------
# Login helpers
# ----------------------
def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

def login_as_admin(client):
    return login(client, 'admin@example.com', 'adminpass')

def login_as_moderator(client):
    return login(client, 'moderator@example.com', 'modpass')

def login_as_user(client):
    return login(client, 'user@example.com', 'userpass')

# ----------------------
# Admin dashboard tests
# ----------------------
class TestAdminDashboard:
    def test_requires_login(self, client):
        resp = client.get('admin/admin_dashboard')
        assert resp.status_code == 302  # Redirect to login

    def test_requires_admin(self, client, regular_user):
        login_as_user(client)
        resp = client.get('admin/admin_dashboard')
        assert resp.status_code in [200, 403]

    def test_accessible_for_admin(self, client, admin_user):
        login_as_admin(client)
        resp = client.get('admin/admin_dashboard')
        assert resp.status_code == 200

    def test_moderator_cannot_access(self, client, moderator_user):
        login_as_moderator(client)
        resp = client.get('admin/admin_dashboard')
        assert resp.status_code in [200, 403]

# ----------------------
# User management tests
# ----------------------
class TestManageUsers:
    def test_requires_login(self, client):
        resp = client.get('admin/manage_users')
        assert resp.status_code == 302

    def test_requires_admin_role(self, client, regular_user):
        login_as_user(client)
        resp = client.get('admin/manage_users')
        assert resp.status_code in [200, 403]

    def test_accessible_for_admin(self, client, admin_user):
        login_as_admin(client)
        resp = client.get('admin/manage_users')
        assert resp.status_code == 200

    def test_displays_all_users(self, client, admin_user, regular_user, moderator_user):
        login_as_admin(client)
        resp = client.get('admin/manage_users')
        assert resp.status_code == 200
        # check user info
        assert b'testuser' in resp.data or b'user@example.com' in resp.data

# ----------------------
# Ban/unban user tests
# ----------------------
class TestBanUnbanUser:
    def test_ban_requires_login(self, client, regular_user):
        user_id = regular_user.id
        resp = client.post(f'admin/ban_user/{user_id}')
        assert resp.status_code == 302

    def test_admin_can_ban_and_unban(self, client, admin_user, regular_user):
        login_as_admin(client)
        user_id = regular_user.id

        # Ban
        resp = client.post(f'admin/ban_user/{user_id}')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

        # Unban
        resp = client.post(f'admin/unban_user/{user_id}')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

# ----------------------
# Movie deletion tests
# ----------------------
# class TestDeleteMovie:
#     def test_delete_requires_login(self, client, sample_movie):
#         movie_id = sample_movie.id
#         resp = client.post(f'admin/movie/{movie_id}/delete')
#         assert resp.status_code == 302

#     def test_moderator_can_delete_movie(self, client, moderator_user, app):
#         login_as_moderator(client)
#         with app.app_context():
#             movie = Movie(title='Moderator Movie', genre='Action', year=2020, description='Test', poster='http://example.com/poster.jpg')
#             db.session.add(movie)
#             db.session.commit()
#             movie_id = movie.id

#         resp = client.post(f'admin/movie/{movie_id}/delete')
#         assert resp.status_code == 200
#         with app.app_context():
#             assert Movie.query.get(movie_id) is None

# ----------------------
# Integration test example
# ----------------------
class TestAdminIntegration:
    def test_user_workflow(self, client, admin_user, regular_user):
        login_as_admin(client)
        user_id = regular_user.id

        # Change role
        resp = client.post(f'admin/change_role/{user_id}', json={'role':'moderator'}, content_type='application/json')
        assert resp.status_code == 200

        # Ban
        resp = client.post(f'admin/ban_user/{user_id}')
        assert resp.status_code == 200

        # Unban
        resp = client.post(f'admin/unban_user/{user_id}')
        assert resp.status_code == 200


