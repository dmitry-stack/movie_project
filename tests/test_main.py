import pytest
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from app.models import User, Movie, Review, PasswordResetToken
from app.extensions import db

# --- Fixtures ----------------------------------------------------------

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def ensure_index_endpoint(app):
    with app.app_context():
        if 'index' not in app.view_functions:
            def _dummy_index():
                return 'OK', 200
            app.add_url_rule('/dummy_index', endpoint='index', view_func=_dummy_index)
        yield


@pytest.fixture
def user(app):
    with app.app_context():
        u = User.query.filter_by(email='user@example.com').first()
        if not u:
            u = User(
                username='testuser',
                email='user@example.com',
                password=generate_password_hash('userpass'),
                role='user'
            )
            db.session.add(u)
            db.session.commit()
        yield User.query.filter_by(email='user@example.com').first()


@pytest.fixture
def admin(app):
    with app.app_context():
        u = User.query.filter_by(email='admin@example.com').first()
        if not u:
            u = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('adminpass'),
                role='admin'
            )
            db.session.add(u)
            db.session.commit()
        yield User.query.filter_by(email='admin@example.com').first()


@pytest.fixture
def movie(app):
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
        yield Movie.query.filter_by(title='Test Movie').first()


# --- Helper Functions --------------------------------------------------

def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


# --- Tests -------------------------------------------------------------

def test_index_access(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_register_new_user(client, app):
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
    r1 = login(client, 'user@example.com', 'userpass')
    assert b'Login successful' in r1.data
    r2 = client.get('/logout', follow_redirects=True)
    assert r2.status_code == 200


def test_dashboard_requires_login(client):
    resp = client.get('/dashboard', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Login' in resp.data


# --- Movie & Review Tests ---------------------------------------------

def test_movies_sort_and_filter(client, app, admin):
    login(client, 'admin@example.com', 'adminpass')
    with app.app_context():
        Movie.query.delete()
        m1 = Movie(title='Test Movie', genre='Action', year=2024, description='D1', poster='p1')
        m2 = Movie(title='Another Movie', genre='Drama', year=2023, description='D2', poster='p2')
        db.session.add_all([m1, m2])
        db.session.commit()

    resp = client.get('/movies?sort=title_asc&genre=Drama')
    assert resp.status_code == 200
    assert b'Another Movie' in resp.data
    assert b'Test Movie' not in resp.data


def test_add_movie_api_failure(client, admin, app):
    login(client, 'admin@example.com', 'adminpass')
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception('API failure')
        resp = client.post('/add_movie', data={'title': 'NoMovie'}, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert Movie.query.filter_by(title='NoMovie').first() is None


def test_add_movie_not_found(client, admin, app):
    login(client, 'admin@example.com', 'adminpass')
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'Response': 'False', 'Error': 'Movie not found!'}
        resp = client.post('/add_movie', data={'title': 'UnknownMovie'}, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert Movie.query.filter_by(title='UnknownMovie').first() is None





# --- Password Reset Tests ---------------------------------------------

def test_password_reset_flow(client, app, user):
    # Request reset
    resp1 = client.post('/request_reset', data={'email': 'user@example.com'}, follow_redirects=True)
    assert b'reset' in resp1.data.lower()

    # Create token manually
    with app.app_context():
        token = PasswordResetToken.generate(user.id)

    # Access reset page with valid token
    resp2 = client.get(f'/reset_password/{token}', follow_redirects=True)
    assert resp2.status_code == 200

    # Reset password
    resp3 = client.post(
        f'/reset_password/{token}',
        data={'password': 'newpass', 'confirm_password': 'newpass'},
        follow_redirects=True
    )
    assert b'reset' in resp3.data.lower()

    # Token should be marked used
    with app.app_context():
        prt = PasswordResetToken.query.filter_by(token=token).first()
        assert prt.used is True


def test_password_reset_invalid_token(client):
    resp = client.get('/reset_password/invalidtoken', follow_redirects=True)
    assert b'invalid' in resp.data.lower()
