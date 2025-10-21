from flask import Blueprint, jsonify, request
from flask_login import login_required
from ..decorators import role_required
import requests
from ..models import Movie
from ..extensions import db
from .main import main

api = Blueprint('api', __name__)


@api.route('/search_movies')
@login_required
@role_required('moderator', 'admin')
def api_search_movies():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Empty query'}), 400

    api_key = "9eb2235f"
    url = f"https://www.omdbapi.com/?apikey={api_key}&s={query}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return jsonify({'error': f'OMDb API error: {e}'}), 500

    if data.get("Response") == "False" and "Too many results" in data.get("Error", ""):
        response2 = requests.get(
            f"https://www.omdbapi.com/?apikey={api_key}&t={query}",
            timeout=5
        )
        data2 = response2.json()
        if data2.get("Response") == "True":
            return jsonify([{
                "title": data2["Title"],
                "year": data2["Year"],
                "imdb_id": data2["imdbID"],
                "poster": data2["Poster"]
            }])
        else:
            return jsonify({'error': "Too many matches. Refine your query."}), 400

    results = []
    for movie in data.get("Search", [])[:5]:
        results.append({
            "title": movie["Title"],
            "year": movie["Year"],
            "imdb_id": movie["imdbID"],
            "poster": movie["Poster"]
        })
    return jsonify(results)



@api.route('/add_movie', methods=['POST'])
@login_required
@role_required('moderator', 'admin')
def api_add_movie():
    data = request.get_json()
    imdb_id = data.get('imdb_id')
    api_key = "9eb2235f"

    if not imdb_id:
        return jsonify({'error': 'imdb_id is not specified'}), 400

    try:
        response = requests.get(f"https://www.omdbapi.com/?i={imdb_id}&apikey={api_key}", timeout=5)
        response.raise_for_status()
        movie_data = response.json()
    except requests.RequestException as e:
        return jsonify({'error': f'Error occured connecting to OMDb API: {e}'}), 500

    if movie_data.get('Response') == 'False':
        return jsonify({'error': f"Movie with an ID {imdb_id} is not found."}), 404
    
    if movie_data.get('Type') != 'movie':
     return jsonify({'error': f"Item with ID {imdb_id} is not a movie (type={movie_data.get('Type')})."}), 400


    existing = Movie.query.filter_by(title=movie_data.get('Title')).first()
    if existing:
        return jsonify({'error': 'This movie is already in the database'}), 400
    
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