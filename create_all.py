from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():

    db.drop_all()
    db.create_all()
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
            email='moderatoremail@gmail.com',
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


