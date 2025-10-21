<<<<<<< HEAD
# from app import db, User, app
# from werkzeug.security import generate_password_hash

# with app.app_context():

#    users= User.query.all()
#    for u in users:
#         print(u.id, u.username, u.role)
from app import db, User, app
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()

    u1 = User(username='user', password=generate_password_hash('user'), role='user')
    u2 = User(username='manager', password=generate_password_hash('manager'), role='manager')
    u3 = User(username='admin', password=generate_password_hash('admin'), role='admin')
    
    db.session.add_all([u1, u2, u3])
    print("Successfully added users.")
    db.session.commit()
=======
from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

# Create the Flask app context
app = create_app()

with app.app_context():
    # Recreate database schema
    db.drop_all()
    db.create_all()

    # Create users with different roles
    users = [
        User(
            username='user',
            password=generate_password_hash('user'),
            email='useremail@gmail.com',
            role='user'
        ),
        User(
            username='moderator',
            password=generate_password_hash('moderator'),
            email='managermail@gmail.com',
            role='moderator'
        ),
        User(
            username='admin',
            password=generate_password_hash('admin'),
            email='adminemail@gmail.com',
            role='admin'
        )
    ]

    db.session.add_all(users)
    db.session.commit()

    print(" Database recreated and default users added successfully!")
# from app import create_app

# app = create_app()

# with app.app_context():
#     print("Registered routes:")
#     for rule in app.url_map.iter_rules():
#         methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
#         endpoint = rule.endpoint
#         print(f"{rule} -> {endpoint} [{methods}]")
>>>>>>> e17068d (first)
