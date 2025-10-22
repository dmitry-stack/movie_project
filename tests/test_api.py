import pytest
import json
from unittest.mock import patch, Mock
from werkzeug.security import generate_password_hash
from app.models import User, Movie


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    from app.extensions import db
    with app.app_context():
        user = User.query.filter_by(email='admin@test.com').first()
        if not user:
            user = User(
                username='admin_test',
                email='admin@test.com',
                password=generate_password_hash('adminpass'),
                role='admin'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
        yield user


@pytest.fixture
def moderator_user(app):
    from app.extensions import db
    with app.app_context():
        user = User.query.filter_by(email='moderator@test.com').first()
        if not user:
            user = User(
                username='moderator_test',
                email='moderator@test.com',
                password=generate_password_hash('modpass'),
                role='moderator'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
        yield user


@pytest.fixture
def regular_user(app):
    from app.extensions import db
    with app.app_context():
        user = User.query.filter_by(email='user@test.com').first()
        if not user:
            user = User(
                username='user_test',
                email='user@test.com',
                password=generate_password_hash('userpass'),
                role='user'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
        yield user


def login_user(client, email, password):
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)



class TestSearchMovies:

    
    
    def test_search_movies_empty_query(self, client, app, moderator_user):
        login_user(client, 'moderator@test.com', 'modpass')
        resp = client.get('/api/search_movies?q=')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
        assert 'Empty query' in data['error']
    
    def test_search_movies_no_query_param(self, client, app, moderator_user):
        
        login_user(client, 'moderator@test.com', 'modpass')
        resp = client.get('/api/search_movies')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
    
    @patch('requests.get')
    def test_search_movies_successful(self, mock_get, client, app, moderator_user):
        
        login_user(client, 'moderator@test.com', 'modpass')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Search": [
                {
                    "Title": "Batman Begins",
                    "Year": "2005",
                    "imdbID": "tt0372784",
                    "Poster": "https://example.com/poster.jpg"
                },
                {
                    "Title": "The Dark Knight",
                    "Year": "2008",
                    "imdbID": "tt0468569",
                    "Poster": "https://example.com/poster2.jpg"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.get('/api/search_movies?q=Batman')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['title'] == 'Batman Begins'
        assert data[0]['year'] == '2005'
        assert data[0]['imdb_id'] == 'tt0372784'
    
    @patch('requests.get')
    def test_search_movies_admin_access(self, mock_get, client, app, admin_user):
       
        login_user(client, 'admin@test.com', 'adminpass')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Search": [{
                "Title": "Inception",
                "Year": "2010",
                "imdbID": "tt1375666",
                "Poster": "https://example.com/poster.jpg"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.get('/api/search_movies?q=Inception')
        assert resp.status_code == 200
    
    @patch('requests.get')
    def test_search_movies_too_many_results_fallback(self, mock_get, client, app, admin_user):
        
        login_user(client, 'admin@test.com', 'adminpass')

        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "Response": "False",
            "Error": "Too many results."
        }
        mock_response1.raise_for_status = Mock()

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "Response": "True",
            "Title": "Batman",
            "Year": "1989",
            "imdbID": "tt0096895",
            "Poster": "https://example.com/batman.jpg"
        }
        mock_response2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response1, mock_response2]
        
        resp = client.get('/api/search_movies?q=Batman')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['title'] == 'Batman'
    
    @patch('requests.get')
    def test_search_movies_too_many_results_no_fallback(self, mock_get, client, app, admin_user):
        login_user(client, 'admin@test.com', 'adminpass')

        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "Response": "False",
            "Error": "Too many results."
        }
        mock_response1.raise_for_status = Mock()
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "Response": "False"
        }
        mock_response2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response1, mock_response2]
        
        resp = client.get('/api/search_movies?q=a')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
        assert 'Too many matches' in data['error']
    

    @patch('requests.get')
    def test_search_movies_limits_to_5_results(self, mock_get, client, app, admin_user):
        
        login_user(client, 'admin@test.com', 'adminpass')

        movies = [
            {
                "Title": f"Movie {i}",
                "Year": "2020",
                "imdbID": f"tt000000{i}",
                "Poster": "https://example.com/poster.jpg"
            }
            for i in range(10)
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Search": movies
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.get('/api/search_movies?q=Movie')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 5
    
    @patch('requests.get')
    def test_search_movies_no_results(self, mock_get, client, app, moderator_user):
        
        login_user(client, 'moderator@test.com', 'modpass')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Search": []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.get('/api/search_movies?q=NonexistentMovie12345')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 0


class TestAddMovie:
    
    
    def test_add_movie_requires_login(self, client):
        
        resp = client.post('/api/add_movie', 
                          json={'imdb_id': 'tt0372784'},
                          content_type='application/json')
        assert resp.status_code == 302  
    
    def test_add_movie_requires_moderator_or_admin(self, client, app, regular_user):
        
        login_user(client, 'user@test.com', 'userpass')
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt0372784'},
                          content_type='application/json')
        assert resp.status_code in [302, 403]
    
    def test_add_movie_missing_imdb_id(self, client, app, moderator_user):
       
        login_user(client, 'moderator@test.com', 'modpass')
        resp = client.post('/api/add_movie',
                          json={},
                          content_type='application/json')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
        assert 'imdb_id is not specified' in data['error']
    
    def test_add_movie_null_imdb_id(self, client, app, moderator_user):
       
        login_user(client, 'moderator@test.com', 'modpass')
        resp = client.post('/api/add_movie',
                          json={'imdb_id': None},
                          content_type='application/json')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
    
    @patch('requests.get')
    def test_add_movie_successful(self, mock_get, client, app, moderator_user):
        
        from app.extensions import db
        login_user(client, 'moderator@test.com', 'modpass')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Type": "movie",
            "Title": "Batman Begins",
            "Year": "2005",
            "Genre": "Action, Crime, Drama",
            "Plot": "After training with his mentor...",
            "Poster": "https://example.com/poster.jpg",
            "imdbID": "tt0372784"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt0372784'},
                          content_type='application/json')
        
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['title'] == 'Batman Begins'

        with app.app_context():
            movie = Movie.query.filter_by(title='Batman Begins').first()
            assert movie is not None
            assert movie.genre == 'Action, Crime, Drama'
            assert movie.year == 2005
    
    @patch('requests.get')
    def test_add_movie_admin_access(self, mock_get, client, app, admin_user):
        
        from app.extensions import db
        login_user(client, 'admin@test.com', 'adminpass')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Type": "movie",
            "Title": "Inception",
            "Year": "2010",
            "Genre": "Action, Sci-Fi",
            "Plot": "A thief who steals secrets...",
            "Poster": "https://example.com/inception.jpg",
            "imdbID": "tt1375666"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt1375666'},
                          content_type='application/json')
        
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
    
    @patch('requests.get')
    def test_add_movie_not_found(self, mock_get, client, app, admin_user):
        
        login_user(client, 'admin@test.com', 'adminpass')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "False",
            "Error": "Movie not found!"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt9999999'},
                          content_type='application/json')
        
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    @patch('requests.get')
    def test_add_movie_not_a_movie_type(self, mock_get, client, app, moderator_user):
       
        login_user(client, 'moderator@test.com', 'modpass')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Type": "series",
            "Title": "Breaking Bad",
            "Year": "2008-2013",
            "imdbID": "tt0903747"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt0903747'},
                          content_type='application/json')
        
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
        assert 'not a movie' in data['error']
        assert 'series' in data['error']
    
    @patch('requests.get')
    def test_add_movie_already_exists(self, mock_get, client, app, admin_user):
       
        from app.extensions import db
        login_user(client, 'admin@test.com', 'adminpass')

        with app.app_context():
            existing_movie = Movie(
                title='The Dark Knight',
                genre='Action, Crime, Drama',
                year=2008,
                description='Batman fights Joker',
                poster='https://example.com/poster.jpg'
            )
            db.session.add(existing_movie)
            db.session.commit()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Type": "movie",
            "Title": "The Dark Knight",
            "Year": "2008",
            "Genre": "Action, Crime, Drama",
            "Plot": "Batman fights Joker",
            "Poster": "https://example.com/poster.jpg",
            "imdbID": "tt0468569"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt0468569'},
                          content_type='application/json')
        
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data
        assert 'already in the database' in data['error']
    
    
    @patch('requests.get')
    def test_add_movie_handles_missing_fields(self, mock_get, client, app, admin_user):
        
        from app.extensions import db
        login_user(client, 'admin@test.com', 'adminpass')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Type": "movie",
            "Title": "Unknown Movie",
            "imdbID": "tt1234567"
          
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resp = client.post('/api/add_movie',
                          json={'imdb_id': 'tt1234567'},
                          content_type='application/json')
        
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

        with app.app_context():
            movie = Movie.query.filter_by(title='Unknown Movie').first()
            assert movie is not None
            assert movie.genre == 'Unknown'
            assert movie.year == 0
            assert movie.description == 'No description available.'


class TestAPIIntegration:
   
    
    @patch('requests.get')
    def test_search_then_add_movie_workflow(self, mock_get, client, app, moderator_user):
        
        from app.extensions import db
        login_user(client, 'moderator@test.com', 'modpass')

        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "Response": "True",
            "Search": [
                {
                    "Title": "Interstellar",
                    "Year": "2014",
                    "imdbID": "tt0816692",
                    "Poster": "https://example.com/interstellar.jpg"
                }
            ]
        }
        search_response.raise_for_status = Mock()

        add_response = Mock()
        add_response.status_code = 200
        add_response.json.return_value = {
            "Response": "True",
            "Type": "movie",
            "Title": "Interstellar",
            "Year": "2014",
            "Genre": "Adventure, Drama, Sci-Fi",
            "Plot": "A team of explorers travel through a wormhole...",
            "Poster": "https://example.com/interstellar.jpg",
            "imdbID": "tt0816692"
        }
        add_response.raise_for_status = Mock()
        
        mock_get.side_effect = [search_response, add_response]

        search_resp = client.get('/api/search_movies?q=Interstellar')
        assert search_resp.status_code == 200
        search_data = json.loads(search_resp.data)
        assert len(search_data) > 0
        imdb_id = search_data[0]['imdb_id']

        add_resp = client.post('/api/add_movie',
                               json={'imdb_id': imdb_id},
                               content_type='application/json')
        assert add_resp.status_code == 200
        add_data = json.loads(add_resp.data)
        assert add_data['success'] is True
        assert add_data['title'] == 'Interstellar'
    
    @patch('requests.get')
    def test_cannot_add_same_movie_twice(self, mock_get, client, app, admin_user):
        
        from app.extensions import db
        login_user(client, 'admin@test.com', 'adminpass')

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": "True",
            "Type": "movie",
            "Title": "The Matrix",
            "Year": "1999",
            "Genre": "Action, Sci-Fi",
            "Plot": "A computer hacker learns...",
            "Poster": "https://example.com/matrix.jpg",
            "imdbID": "tt0133093"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        resp1 = client.post('/api/add_movie',
                           json={'imdb_id': 'tt0133093'},
                           content_type='application/json')
        assert resp1.status_code == 200

        resp2 = client.post('/api/add_movie',
                           json={'imdb_id': 'tt0133093'},
                           content_type='application/json')
        assert resp2.status_code == 400
        data = json.loads(resp2.data)
        assert 'already in the database' in data['error']