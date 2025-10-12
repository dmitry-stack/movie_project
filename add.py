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
