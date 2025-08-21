from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    u_id = db.Column(db.Integer, primary_key=True)
    u_name = db.Column(db.String(50), nullable=False)
    u_email = db.Column(db.String(120), unique=True, nullable=False)
    u_pwd = db.Column(db.String(200), nullable=False)
    u_phone = db.Column(db.String(15), nullable=False)
    u_address = db.Column(db.String(200), nullable=False)
    u_role = db.Column(db.String(20), nullable=False)  # 'admin' or 'user'
    u_pincode = db.Column(db.String(10), nullable=True)
    u_bookings = db.relationship('ReservedSpot', backref='user', lazy=True) # because a user can have multiple bookings



class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    
    pl_id = db.Column(db.Integer, primary_key=True)
    pl_location = db.Column(db.String(100), nullable=False)
    pl_address = db.Column(db.String(200), nullable=False)
    pl_price = db.Column(db.Float, nullable=False)
    pl_pincode = db.Column(db.String(10), nullable=False)
    pl_maxspots = db.Column(db.Integer, nullable=False)
    pl_spots_linked = db.relationship('ParkingSpot', backref='parking_lot', cascade="all, delete-orphan", lazy=True) # because a parking lot can have multiple spots


class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    
    ps_id = db.Column(db.Integer, primary_key=True)
    ps_status = db.Column(db.String(20), nullable=False)  # 'A' or 'O'
    ps_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.pl_id'), nullable=False)
    ps_spot_reservation = db.relationship('ReservedSpot', backref='parking_spot', lazy=True)# because a parking spot can have multiple reservations


class ReservedSpot(db.Model):
    __tablename__ = 'reserved_spot'
    
    rs_id = db.Column(db.Integer, primary_key=True)
    rs_user_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    rs_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.ps_id'), nullable=False)
    rs_time_checked_in = db.Column(db.DateTime, nullable=False)
    rs_time_checked_out = db.Column(db.DateTime, nullable=True)
    rs_hourly_rate = db.Column(db.Float, nullable=False)
    rs_total_amount = db.Column(db.Float, nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
