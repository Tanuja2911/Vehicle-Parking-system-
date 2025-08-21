from flask import render_template, request, redirect, session, flash, url_for
from models import db, ParkingLot, ParkingSpot, User, ReservedSpot
from functools import wraps

def register_admin_routes(app):
    # Admin-only access decorator
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('user_role') != 'admin':
                flash('Admin access required.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # Admin dashboard
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
     name = session.get('full_name')
     lots = ParkingLot.query.all()

     for lot in lots:
        # Calculate total spots and available spots for each lot
        total = len(lot.pl_spots_linked)
        available = sum(1 for spot in lot.pl_spots_linked if spot.ps_status == 'A')
        lot.total_spots_allowed = total
        lot.total_spots_available = available
      

     users = User.query.filter_by(u_role='user').all()
     return render_template('admin_dashboard.html', name=name, lots=lots, users=users)

    # Create a new parking lot
    @app.route('/admin/create-lot', methods=['GET', 'POST'])
    @admin_required
    def create_parking_lot():
        if request.method == 'POST':
            try:
                location = request.form['location']
                address = request.form['address']
                pincode = request.form['pincode']
                price = float(request.form['price'])
                total_spots = int(request.form['total_spots'])

                new_lot = ParkingLot(
                    pl_location=location,
                    pl_address=address,
                    pl_pincode=pincode,
                    pl_price=price,
                    pl_maxspots=total_spots
                )
                db.session.add(new_lot)
                db.session.flush()

                spots = [ParkingSpot(ps_status='A', ps_lot_id=new_lot.pl_id) for _ in range(total_spots)]
                db.session.add_all(spots)

                db.session.commit()
                return redirect(url_for('admin_dashboard'))

            except (ValueError, KeyError) as e:
                db.session.rollback()
                flash(f'Invalid input: {e}', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Unexpected error: {e}', 'danger')

        return render_template('create_lot.html')

    # Edits an existing parking lot
    @app.route('/admin/edit-lot/<int:lot_id>', methods=['GET', 'POST'])
    @admin_required
    def edit_parking_lot(lot_id):
        lot = ParkingLot.query.get_or_404(lot_id)

        if request.method == 'POST':
            try:
                lot.pl_location = request.form['location']
                lot.pl_address = request.form['address']
                lot.pl_pincode = request.form['pincode']
                lot.pl_price = float(request.form['rate'])

                db.session.commit()
                flash('Parking lot updated successfully!', 'success')
                return redirect(url_for('admin_dashboard'))

            except (ValueError, KeyError):
                db.session.rollback()
            except Exception as e:
                db.session.rollback()
                flash(f'Unexpected error: {e}', 'danger')

        return render_template('edit_lot.html', lot=lot)

    # Deletes a parking lot
    @app.route('/admin/delete-lot/<int:lot_id>', methods=['POST'])
    @admin_required
    def delete_parking_lot(lot_id):
        lot = ParkingLot.query.get_or_404(lot_id)
        occupied_spots = any(spot.ps_status == 'O' for spot in lot.pl_spots_linked)

        if occupied_spots:
            flash('Cannot delete a lot with occupied spots.')
        else:
            try:
                db.session.delete(lot)
                db.session.commit()
                flash('Parking lot deleted.', 'info')
            except Exception as e:
                db.session.rollback()
                flash(f'Error deleting lot: {e}', 'danger')

        return redirect(url_for('admin_dashboard'))

    # Views details of a parking spot
    @app.route('/admin/view-spot/<int:spot_id>')
    @admin_required
    def view_spot(spot_id):
        spot = ParkingSpot.query.get_or_404(spot_id)
        return render_template('view_spots.html', spot=spot)

    # Deletes a parking spot 
    @app.route('/admin/delete-spot/<int:spot_id>', methods=['POST'])
    @admin_required
    def delete_spot(spot_id):
        spot = ParkingSpot.query.get_or_404(spot_id)

        if spot.ps_status == 'O':
            flash('Cannot delete an occupied spot.', 'danger')
        else:
            try:
                db.session.delete(spot)
                db.session.commit()
                flash('Parking spot deleted.', 'info')
            except Exception as e:
                db.session.rollback()
                flash(f'Error deleting spot: {e}', 'danger')

        return redirect(url_for('admin_dashboard'))
    
    
    # Views details of a reserved spot
    @app.route('/admin/spot-reservation/<int:spot_id>')
    @admin_required
    def spot_reservation_details(spot_id):
        reservation = ReservedSpot.query.filter_by(rs_spot_id=spot_id, rs_time_checked_out=None).first()
        if not reservation:
            return redirect(url_for('admin_dashboard'))
        return render_template('o_spot.html',reservation=reservation, spot=reservation.parking_spot, user=reservation.user)
    
    
    # Views all users
    @app.route('/admin/users')
    @admin_required
    def view_users():
      users = User.query.filter_by(u_role='user').all()
      return render_template('admin_users.html', users=users)
    

    #searches
    @app.route('/admin/search', methods=['GET', 'POST'])
    @admin_required
    def admin_search():
     found_lots = []
     found_user = None
     active_reservation = None
     found_spot = None


     if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_value = request.form.get('search_value')

        try:
            if search_type == 'location':
                found_lots = ParkingLot.query.filter(
                    ParkingLot.pl_location.ilike(f"%{search_value}%")
                ).all()

            elif search_type == 'lot_id':
                found_lot = ParkingLot.query.get(int(search_value))
                if found_lot:
                    found_lots = [found_lot]
                else:
                    flash("Parking lot not found.", "warning")

            elif search_type == 'pincode':
                found_lots = ParkingLot.query.filter(
                    ParkingLot.pl_pincode.ilike(f"%{search_value}%")
                ).all()

            elif search_type == 'user_id':
                found_user = User.query.get(int(search_value))
                if found_user:
                    active_reservation = ReservedSpot.query.filter_by(
                        rs_user_id=found_user.u_id,
                        rs_time_checked_out=None
                    ).first()
                else:
                    flash("User not found.", "warning")
           

            elif search_type == 'spot_id':
                if search_value.isdigit():
                    found_spot = ParkingSpot.query.get(int(search_value))
                    if not found_spot:
                        flash("Spot not found.", "warning")
                else:
                    flash("Invalid Spot ID.", "danger")

            else:
                flash("Invalid search type.", "danger")

        except ValueError:
            flash("Invalid input format for this search type.", "danger")

     return render_template(
        'admin_search.html',found_lots=found_lots,found_user=found_user,active_reservation=active_reservation,found_spot=found_spot)
    
 

    
