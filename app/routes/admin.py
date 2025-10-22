from flask import Blueprint, jsonify, request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from ..decorators import role_required
from ..models import User,Review, Movie
from ..extensions import db

admin = Blueprint('admin', __name__)


@admin.route('/admin_dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('admin.html')


@admin.route('/manage_users')
@login_required
@role_required('admin')
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)


@admin.route('/ban_user/<int:user_id>', methods=['POST'])
@login_required
def ban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        return jsonify({'success': False, 'error': 'Cannot ban another administrator'}), 400
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot ban yourself'}), 400
    
    user.is_banned = True
    db.session.commit()
    return jsonify({'success': True, 'message': f'User {user.username} has been banned'})


@admin.route('/unban_user/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    return jsonify({'success': True, 'message': f'User {user.username} has been unbanned'})


@admin.route('/change_role/<int:user_id>', methods=['POST'])
@login_required
def change_role(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot change your own role'}), 400
    
    data = request.get_json() or {}
    new_role = data.get('role')
    valid_roles = ['user', 'moderator', 'admin']
    
    if new_role not in valid_roles:
        return jsonify({'success': False, 'error': 'Invalid role specified'}), 400
    
    old_role = user.role
    user.role = new_role
    db.session.commit()
    return jsonify({'success': True, 'message': f'User {user.username} role changed from {old_role} to {new_role}'})


@admin.route('/moderator_dashboard')
@login_required
@role_required('moderator', 'admin')
def moderator_dashboard():
    return render_template('manager.html')


@admin.route('/movie/<int:movie_id>/delete', methods=['POST'])
@login_required
def delete_movie(movie_id):
    try:
        if current_user.role not in ['admin', 'moderator']:
            flash("You don't have permission to delete movies.", "danger")
            return redirect(url_for('main.movie_details', movie_id=movie_id))

        movie = Movie.query.get_or_404(movie_id)
        Review.query.filter_by(movie_id=movie.id).delete()
        db.session.delete(movie)
        db.session.commit()

        flash(f"Movie '{movie.title}' has been deleted.", "success")
        return redirect(url_for('main.movies'))
    except Exception as e:
        flash(f"Error deleting movie: {str(e)}", "danger")
        return redirect(url_for('main.movies'))
