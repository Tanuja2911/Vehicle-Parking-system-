from flask import render_template, request, redirect,session
from models import db, User
from sqlalchemy.exc import IntegrityError

def auth(app):
 @app.route('/register', methods=['GET', 'POST'])
 def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone_number')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        new_user = User(
            u_name=name,
            u_email=email.lower(),
            u_pwd=password,
            u_phone=phone,
            u_address=address,
            u_role='user',
            u_pincode=pincode            
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')
        
        except IntegrityError as e:
            db.session.rollback()
            return render_template('register.html', message="Oops,Email already exists.")

    return render_template('register.html')
 
 
 @app.route('/login', methods=['GET', 'POST'])
 def login():
    if request.method == 'POST':
        # it Gets form data
        email_input = request.form.get('email')
        password_input = request.form.get('password')
        matched_user = User.query.filter_by(u_email=email_input, u_pwd=password_input).first()

        if matched_user:
            # Saves the user info in session
            session['user_id'] = matched_user.u_id
            session['user_name'] = matched_user.u_name
            session['user_role'] = matched_user.u_role
            session['user_email'] = matched_user.u_email

            # Redirects depending on role
            if matched_user.u_role == 'admin':
                return redirect('/admin/dashboard')
            else:
                return redirect('/user/dashboard')
        else:
            # Login failed
            return render_template('login.html', message="Invalid login details!")
    return render_template('login.html')
 
 
 @app.route('/logout')
 def logout():
    # Clears the session and logs out the user
    session.clear()
    return redirect('/login')


          


        
        