from app import db, User, app

with app.app_context():
    users = User.query.all()
    for u in users:
        print(u.id, u.username, u.role)
