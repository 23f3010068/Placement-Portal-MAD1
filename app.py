from flask import Flask
from models.models import db, User
app = None

def setup_app():
    global app
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement_portal.sqlite3"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    app.app_context().push()
    
    with app.app_context():
        db.create_all()
        create_admin()
        
def create_admin():
    admin_email = "admin@gmail.com"
    admin = User.query.filter_by(role='admin').first() 
    if not admin:
        new_admin = User(
            email=admin_email,
            password="admin123",
            role="admin",
            is_active=True)
        db.session.add(new_admin)
        db.session.commit()

setup_app()
from backend.routes import *

if __name__ == "__main__":
    app.run(debug=True)

