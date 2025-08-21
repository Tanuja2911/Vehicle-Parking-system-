from flask import render_template, request, redirect, session, flash, url_for
from models import db, ParkingLot, ParkingSpot, User, ReservedSpot
from datetime import datetime
from functools import wraps

def user_dashboard(app):
    def user_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('user_role') != 'user':
                flash('User access required.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    

    @app.route('/user/dashboard')
    @user_required
    def dashboard():
        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)
        parking_lots = ParkingLot.query.all()
        reservations = ReservedSpot.query.filter_by(rs_user_id=user_id).order_by(ReservedSpot.rs_time_checked_in.desc()).all()
        lots_with_availability = []
        for lot in parking_lots:
         available = sum(1 for spot in lot.pl_spots_linked if spot.ps_status == 'A')
         lots_with_availability.append({
            'lot': lot,
            'available_count': available
        })
        return render_template('user_dashboard.html', user=user, reservations=reservations, ParkingLots=parking_lots,lots=lots_with_availability)


    @app.route('/user/book-spot/<int:lot_id>', methods=['GET', 'POST'])
    @user_required
    def book_parking_spot(lot_id):
        lot = ParkingLot.query.get_or_404(lot_id)

        if request.method == 'POST':
            user_id = session.get('user_id')
            user = User.query.get(user_id)
            vehicle_number = request.form.get('vehicle_number')

            if not vehicle_number:
                flash("Vehicle number is required.", "warning")
                return redirect(url_for('dashboard'))

            free_spot = ParkingSpot.query.filter_by(ps_lot_id=lot_id, ps_status='A').first()
            

            if not free_spot:
                flash("No available spots in this lot.", "warning")
                return redirect(url_for('dashboard'))

            try:
                free_spot.ps_status = 'O'
                reservation = ReservedSpot(
                    rs_user_id=user_id,
                    rs_spot_id=free_spot.ps_id,
                    rs_time_checked_in=datetime.utcnow(),
                    vehicle_number=vehicle_number,
                    rs_hourly_rate=lot.pl_price,
                    rs_total_amount=0.0
                )

                db.session.add(reservation)
                db.session.commit()
                flash("Spot successfully booked!", "success")
                return redirect(url_for('dashboard'))

            except Exception as e:
                db.session.rollback()
                flash(f"Error during booking: {str(e)}", "danger")
                return redirect(url_for('dashboard'))
        free_spot = ParkingSpot.query.filter_by(ps_lot_id=lot_id, ps_status='A').first()
        user = User.query.get(session.get('user_id'))

        return render_template('book.html', lot=lot, spot=free_spot, user=user)



    @app.route('/user/release-spot/<int:reservation_id>', methods=['POST'])
    @user_required
    def release_parking_spot(reservation_id):
        user_id = session.get('user_id')
        reservation = ReservedSpot.query.filter_by(rs_id=reservation_id, rs_user_id=user_id).first()

        if not reservation:
            flash("Reservation not found or unauthorized.", "danger")
            return redirect(url_for('dashboard'))

        if not reservation.rs_time_checked_out:
            reservation.rs_time_checked_out = datetime.utcnow()

            duration_hours = (reservation.rs_time_checked_out - reservation.rs_time_checked_in).total_seconds() / 3600
            reservation.rs_total_amount = round(duration_hours * reservation.rs_hourly_rate, 2)

            parking_spot = ParkingSpot.query.get(reservation.rs_spot_id)
            if parking_spot:
                parking_spot.ps_status = 'A'

            try:
                db.session.commit()
                flash("Spot successfully released!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error during release: {str(e)}", "danger")

        return render_template('release_spot.html', reservation=reservation)
    @app.route('/delete_parking/<int:reservation_id>', methods=['POST'])
    @user_required
    def delete_parking_history(reservation_id):
        user_id = session.get('user_id')
        reservation = ReservedSpot.query.filter_by(rs_id=reservation_id, rs_user_id=user_id).first()

        if not reservation:
            flash("Reservation not found or unauthorized.", "danger")
            return redirect(url_for('dashboard'))

        try:
            db.session.delete(reservation)
            db.session.commit()
            flash("Reservation deleted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting reservation: {str(e)}", "danger")

        return redirect(url_for('dashboard'))

    
 




   
