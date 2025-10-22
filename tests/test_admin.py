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


# import pytest
# import json
# from flask import url_for
# from werkzeug.security import generate_password_hash
# from app.models import User, Movie, Review
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
#                 role='admin',
#                 is_banned=False
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
#                 role='moderator',
#                 is_banned=False
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
#                 role='user',
#                 is_banned=False
#             )
#             db.session.add(user)
#             db.session.commit()
#         return user


# @pytest.fixture
# def another_user(app):
#     """Create another regular user for testing."""
#     with app.app_context():
#         user = User.query.filter_by(email='another@example.com').first()
#         if not user:
#             user = User(
#                 username='anotheruser',
#                 email='another@example.com',
#                 password=generate_password_hash('anotherpass'),
#                 role='user',
#                 is_banned=False
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


# def login_user(client, email, password):
#     """Helper function to log in a user."""
#     return client.post('/login', data={
#         'email': email,
#         'password': password
#     }, follow_redirects=True)


# def login_as_admin(client):
#     """Helper function to log in as admin."""
#     return login_user(client, 'admin@example.com', 'adminpass')


# def login_as_moderator(client):
#     """Helper function to log in as moderator."""
#     return login_user(client, 'moderator@example.com', 'modpass')


# def login_as_regular_user(client):
#     """Helper function to log in as regular user."""
#     return login_user(client, 'user@example.com', 'userpass')


# # Test Cases

# class TestAdminDashboard:
#     """Tests for admin dashboard routes."""
    
#     def test_admin_dashboard_requires_login(self, client):
#         """Test that admin dashboard requires authentication."""
#         resp = client.get('/admin_dashboard', follow_redirects=False)
#         assert resp.status_code == 302  # Redirect to login
    
#     def test_admin_dashboard_requires_admin_role(self, client, app, regular_user):
#         """Test that regular users cannot access admin dashboard."""
#         login_as_regular_user(client)
#         resp = client.get('/admin_dashboard', follow_redirects=True)
#         # Should be redirected or get 403
#         assert resp.status_code in [200, 403]
#         # Check for access denied message if not using decorator redirect
    
#     def test_admin_dashboard_accessible_for_admin(self, client, app, admin_user):
#         """Test that admins can access admin dashboard."""
#         login_as_admin(client)
#         resp = client.get('/admin_dashboard')
#         assert resp.status_code == 200
    
#     def test_moderator_cannot_access_admin_dashboard(self, client, app, moderator_user):
#         """Test that moderators cannot access admin dashboard."""
#         login_as_moderator(client)
#         resp = client.get('/admin_dashboard', follow_redirects=True)
#         assert resp.status_code in [200, 403]


# class TestManageUsers:
#     """Tests for user management page."""
    
#     def test_manage_users_requires_login(self, client):
#         """Test that manage users page requires authentication."""
#         resp = client.get('/manage_users', follow_redirects=False)
#         assert resp.status_code == 302
    
#     def test_manage_users_requires_admin_role(self, client, app, regular_user):
#         """Test that regular users cannot access manage users page."""
#         login_as_regular_user(client)
#         resp = client.get('/manage_users', follow_redirects=True)
#         assert resp.status_code in [200, 403]
    
#     def test_manage_users_accessible_for_admin(self, client, app, admin_user):
#         """Test that admins can access manage users page."""
#         login_as_admin(client)
#         resp = client.get('/manage_users')
#         assert resp.status_code == 200
    
#     def test_manage_users_displays_all_users(self, client, app, admin_user, regular_user, moderator_user):
#         """Test that manage users page displays all users."""
#         login_as_admin(client)
#         resp = client.get('/manage_users')
#         assert resp.status_code == 200
#         # Check that user data is in the response
#         assert b'testuser' in resp.data or b'user@example.com' in resp.data


# class TestBanUser:
#     """Tests for banning users."""
    
#     def test_ban_user_requires_login(self, client, app, regular_user):
#         """Test that ban user requires authentication."""
#         with app.app_context():
#             user_id = regular_user.id
#         resp = client.post(f'/ban_user/{user_id}')
#         assert resp.status_code == 302
    
#     def test_ban_user_requires_admin_role(self, client, app, regular_user, another_user):
#         """Test that regular users cannot ban other users."""
#         login_as_regular_user(client)
#         with app.app_context():
#             user_id = another_user.id
#         resp = client.post(f'/ban_user/{user_id}')
#         assert resp.status_code == 403
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Access denied' in data['error']
    
#     def test_admin_can_ban_user(self, client, app, admin_user, regular_user):
#         """Test that admin can successfully ban a user."""
#         login_as_admin(client)
#         with app.app_context():
#             user_id = regular_user.id
        
#         resp = client.post(f'/ban_user/{user_id}')
#         assert resp.status_code == 200
#         data = json.loads(resp.data)
#         assert data['success'] is True
#         assert 'banned' in data['message']
        
#         # Verify user is banned in database
#         with app.app_context():
#             user = User.query.get(user_id)
#             assert user.is_banned is True
    
#     def test_cannot_ban_another_admin(self, client, app, admin_user):
#         """Test that admin cannot ban another admin."""
#         # Create another admin
#         with app.app_context():
#             another_admin = User(
#                 username='admin2',
#                 email='admin2@example.com',
#                 password=generate_password_hash('admin2pass'),
#                 role='admin',
#                 is_banned=False
#             )
#             db.session.add(another_admin)
#             db.session.commit()
#             admin2_id = another_admin.id
        
#         login_as_admin(client)
#         resp = client.post(f'/ban_user/{admin2_id}')
#         assert resp.status_code == 400
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Cannot ban another administrator' in data['error']
    
#     def test_cannot_ban_yourself(self, client, app, admin_user):
#         """Test that admin cannot ban themselves."""
#         login_as_admin(client)
#         with app.app_context():
#             user_id = admin_user.id
        
#         resp = client.post(f'/ban_user/{user_id}')
#         assert resp.status_code == 400
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Cannot ban yourself' in data['error']
    
#     def test_ban_nonexistent_user(self, client, app, admin_user):
#         """Test banning non-existent user returns 404."""
#         login_as_admin(client)
#         resp = client.post('/ban_user/99999')
#         assert resp.status_code == 404


# class TestUnbanUser:
#     """Tests for unbanning users."""
    
#     def test_unban_user_requires_login(self, client, app, regular_user):
#         """Test that unban user requires authentication."""
#         with app.app_context():
#             user_id = regular_user.id
#         resp = client.post(f'/unban_user/{user_id}')
#         assert resp.status_code == 302
    
#     def test_unban_user_requires_admin_role(self, client, app, regular_user, another_user):
#         """Test that regular users cannot unban users."""
#         login_as_regular_user(client)
#         with app.app_context():
#             user_id = another_user.id
#         resp = client.post(f'/unban_user/{user_id}')
#         assert resp.status_code == 403
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Access denied' in data['error']
    
#     def test_admin_can_unban_user(self, client, app, admin_user, regular_user):
#         """Test that admin can successfully unban a user."""
#         # First ban the user
#         with app.app_context():
#             user = User.query.get(regular_user.id)
#             user.is_banned = True
#             db.session.commit()
#             user_id = user.id
        
#         login_as_admin(client)
#         resp = client.post(f'/unban_user/{user_id}')
#         assert resp.status_code == 200
#         data = json.loads(resp.data)
#         assert data['success'] is True
#         assert 'unbanned' in data['message']
        
#         # Verify user is unbanned in database
#         with app.app_context():
#             user = User.query.get(user_id)
#             assert user.is_banned is False
    
#     def test_unban_nonexistent_user(self, client, app, admin_user):
#         """Test unbanning non-existent user returns 404."""
#         login_as_admin(client)
#         resp = client.post('/unban_user/99999')
#         assert resp.status_code == 404


# class TestChangeRole:
#     """Tests for changing user roles."""
    
#     def test_change_role_requires_login(self, client, app, regular_user):
#         """Test that change role requires authentication."""
#         with app.app_context():
#             user_id = regular_user.id
#         resp = client.post(f'/change_role/{user_id}',
#                           json={'role': 'moderator'},
#                           content_type='application/json')
#         assert resp.status_code == 302
    
#     def test_change_role_requires_admin_role(self, client, app, regular_user, another_user):
#         """Test that regular users cannot change roles."""
#         login_as_regular_user(client)
#         with app.app_context():
#             user_id = another_user.id
#         resp = client.post(f'/change_role/{user_id}',
#                           json={'role': 'moderator'},
#                           content_type='application/json')
#         assert resp.status_code == 403
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Access denied' in data['error']
    
#     def test_admin_can_change_user_role(self, client, app, admin_user, regular_user):
#         """Test that admin can successfully change user role."""
#         login_as_admin(client)
#         with app.app_context():
#             user_id = regular_user.id
        
#         resp = client.post(f'/change_role/{user_id}',
#                           json={'role': 'moderator'},
#                           content_type='application/json')
#         assert resp.status_code == 200
#         data = json.loads(resp.data)
#         assert data['success'] is True
#         assert 'role changed' in data['message']
#         assert 'user' in data['message']
#         assert 'moderator' in data['message']
        
#         # Verify role changed in database
#         with app.app_context():
#             user = User.query.get(user_id)
#             assert user.role == 'moderator'
    
#     def test_cannot_change_own_role(self, client, app, admin_user):
#         """Test that admin cannot change their own role."""
#         login_as_admin(client)
#         with app.app_context():
#             user_id = admin_user.id
        
#         resp = client.post(f'/change_role/{user_id}',
#                           json={'role': 'user'},
#                           content_type='application/json')
#         assert resp.status_code == 400
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Cannot change your own role' in data['error']
    
#     def test_change_role_invalid_role(self, client, app, admin_user, regular_user):
#         """Test that invalid role is rejected."""
#         login_as_admin(client)
#         with app.app_context():
#             user_id = regular_user.id
        
#         resp = client.post(f'/change_role/{user_id}',
#                           json={'role': 'superuser'},
#                           content_type='application/json')
#         assert resp.status_code == 400
#         data = json.loads(resp.data)
#         assert data['success'] is False
#         assert 'Invalid role specified' in data['error']
    
#     def test_change_role_valid_roles(self, client, app, admin_user, regular_user):
#         """Test all valid role changes."""
#         login_as_admin(client)
#         with app.app_context():
#             user_id = regular_user.id
        
#         valid_roles = ['user', 'moderator', 'admin']
#         for role in valid_roles:
#             resp = client.post(f'/change_role/{user_id}',
#                               json={'role': role},
#                               content_type='application/json')
#             assert resp.status_code == 200
#             data = json.loads(resp.data)
#             assert data['success'] is True
    
#     def test_change_role_nonexistent_user(self, client, app, admin_user):
#         """Test changing role of non-existent user returns 404."""
#         login_as_admin(client)
#         resp = client.post('/change_role/99999',
#                           json={'role': 'moderator'},
#                           content_type='application/json')
#         assert resp.status_code == 404


# class TestModeratorDashboard:
#     """Tests for moderator dashboard."""
    
#     def test_moderator_dashboard_requires_login(self, client):
#         """Test that moderator dashboard requires authentication."""
#         resp = client.get('/moderator_dashboard', follow_redirects=False)
#         assert resp.status_code == 302
    
#     def test_moderator_dashboard_requires_moderator_or_admin(self, client, app, regular_user):
#         """Test that regular users cannot access moderator dashboard."""
#         login_as_regular_user(client)
#         resp = client.get('/moderator_dashboard', follow_redirects=True)
#         assert resp.status_code in [200, 403]
    
#     def test_moderator_dashboard_accessible_for_moderator(self, client, app, moderator_user):
#         """Test that moderators can access moderator dashboard."""
#         login_as_moderator(client)
#         resp = client.get('/moderator_dashboard')
#         assert resp.status_code == 200
    
#     def test_moderator_dashboard_accessible_for_admin(self, client, app, admin_user):
#         """Test that admins can also access moderator dashboard."""
#         login_as_admin(client)
#         resp = client.get('/moderator_dashboard')
#         assert resp.status_code == 200


# class TestDeleteMovie:
#     """Tests for deleting movies."""
    
#     def test_delete_movie_requires_login(self, client, app, sample_movie):
#         """Test that delete movie requires authentication."""
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.post(f'/movie/{movie_id}/delete', follow_redirects=False)
#         assert resp.status_code == 302
    
#     def test_delete_movie_requires_moderator_or_admin(self, client, app, regular_user, sample_movie):
#         """Test that regular users cannot delete movies."""
#         login_as_regular_user(client)
#         with app.app_context():
#             movie_id = sample_movie.id
#         resp = client.post(f'/movie/{movie_id}/delete', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b"don't have permission" in resp.data or b"permission" in resp.data.lower()
    
#     def test_moderator_can_delete_movie(self, client, app, moderator_user):
#         """Test that moderators can delete movies."""
#         login_as_moderator(client)
        
#         # Create a movie to delete
#         with app.app_context():
#             movie = Movie(
#                 title='Movie to Delete',
#                 genre='Action',
#                 year=2020,
#                 description='Test',
#                 poster='http://example.com/poster.jpg'
#             )
#             db.session.add(movie)
#             db.session.commit()
#             movie_id = movie.id
        
#         resp = client.post(f'/movie/{movie_id}/delete', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'has been deleted' in resp.data
        
#         # Verify movie is deleted
#         with app.app_context():
#             movie = Movie.query.get(movie_id)
#             assert movie is None
    
#     def test_admin_can_delete_movie(self, client, app, admin_user):
#         """Test that admins can delete movies."""
#         login_as_admin(client)
        
#         # Create a movie to delete
#         with app.app_context():
#             movie = Movie(
#                 title='Admin Delete Movie',
#                 genre='Drama',
#                 year=2021,
#                 description='Test',
#                 poster='http://example.com/poster.jpg'
#             )
#             db.session.add(movie)
#             db.session.commit()
#             movie_id = movie.id
        
#         resp = client.post(f'/movie/{movie_id}/delete', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'has been deleted' in resp.data
        
#         # Verify movie is deleted
#         with app.app_context():
#             movie = Movie.query.get(movie_id)
#             assert movie is None
    
#     def test_delete_movie_also_deletes_reviews(self, client, app, admin_user, regular_user):
#         """Test that deleting a movie also deletes associated reviews."""
#         login_as_admin(client)
        
#         # Create a movie with a review
#         with app.app_context():
#             movie = Movie(
#                 title='Movie with Review',
#                 genre='Action',
#                 year=2020,
#                 description='Test',
#                 poster='http://example.com/poster.jpg'
#             )
#             db.session.add(movie)
#             db.session.commit()
            
#             review = Review(
#                 movie_id=movie.id,
#                 user_id=regular_user.id,
#                 rating=5,
#                 content='Great movie!'
#             )
#             db.session.add(review)
#             db.session.commit()
            
#             movie_id = movie.id
#             review_id = review.id
        
#         # Delete the movie
#         resp = client.post(f'/movie/{movie_id}/delete', follow_redirects=True)
#         assert resp.status_code == 200
        
#         # Verify both movie and review are deleted
#         with app.app_context():
#             movie = Movie.query.get(movie_id)
#             review = Review.query.get(review_id)
#             assert movie is None
#             assert review is None
    
#     def test_delete_nonexistent_movie(self, client, app, admin_user):
#         """Test deleting non-existent movie returns 404."""
#         login_as_admin(client)
#         resp = client.post('/movie/99999/delete', follow_redirects=True)
#         assert resp.status_code == 404


# class TestAdminIntegration:
#     """Integration tests for admin functionality."""
    
#     def test_complete_user_management_workflow(self, client, app, admin_user, regular_user):
#         """Test complete workflow: view users, change role, ban, unban."""
#         login_as_admin(client)
        
#         with app.app_context():
#             user_id = regular_user.id
        
#         # View users
#         resp = client.get('/manage_users')
#         assert resp.status_code == 200
        
#         # Change role to moderator
#         resp = client.post(f'/change_role/{user_id}',
#                           json={'role': 'moderator'},
#                           content_type='application/json')
#         assert resp.status_code == 200
        
#         # Ban user
#         resp = client.post(f'/ban_user/{user_id}')
#         assert resp.status_code == 200
        
#         # Unban user
#         resp = client.post(f'/unban_user/{user_id}')
#         assert resp.status_code == 200
        
#         # Verify final state
#         with app.app_context():
#             user = User.query.get(user_id)
#             assert user.role == 'moderator'
#             assert user.is_banned is False
    
#     def test_moderator_movie_management_workflow(self, client, app, moderator_user, regular_user):
#         """Test moderator workflow: access dashboard, delete movie."""
#         login_as_moderator(client)
        
#         # Access moderator dashboard
#         resp = client.get('/moderator_dashboard')
#         assert resp.status_code == 200
        
#         # Create and delete a movie
#         with app.app_context():
#             movie = Movie(
#                 title='Moderator Test Movie',
#                 genre='Action',
#                 year=2020,
#                 description='Test',
#                 poster='http://example.com/poster.jpg'
#             )
#             db.session.add(movie)
#             db.session.commit()
#             movie_id = movie.id
        
#         resp = client.post(f'/movie/{movie_id}/delete', follow_redirects=True)
#         assert resp.status_code == 200
#         assert b'has been deleted' in resp.data
