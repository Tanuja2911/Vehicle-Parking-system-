from flask import Flask, render_template
import os
from models import db, User
from controllers.auth import auth
from controllers.admin import register_admin_routes
from controllers.user import user_dashboard

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'parking_app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key='key'

db.init_app(app)

with app.app_context():
    db.create_all() 

    if not User.query.filter_by(u_role='admin').first():
        admin = User(
            u_name='Admin User',
            u_email='admin@parking.com',
            u_pwd=123456,
            u_phone='9999999999',
            u_address='Admin Address',
            u_role='admin'
        )
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')

auth(app)
register_admin_routes(app)
user_dashboard(app)

if __name__ == '__main__':
    app.run(debug=True)
