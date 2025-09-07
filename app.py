# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret")

# DATABASE: use DATABASE_URL from Railway. Fallback to sqlite for local testing.
database_url = os.environ.get("DATABASE_URL", "sqlite:///local_dev.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# MODELS
# --------------------------
class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    no_of_trays = db.Column(db.Integer, nullable=False)
    sold_price_per_unit = db.Column(db.Float, nullable=False)
    buyer_name = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class StaffUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # vallam_chennai / kerala / ceo

class AvailableStock(db.Model):
    __tablename__ = 'available_stock'
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String, nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    no_of_trays = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class DirectInbound(db.Model):
    __tablename__ = 'direct_inbound'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    whole_weight = db.Column(db.Float, nullable=False)
    no_of_trays = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    seller_name = db.Column(db.String, nullable=True)

class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    perday_salary = db.Column(db.Float, nullable=False)
    days_worked = db.Column(db.Integer, nullable=False)
    advance = db.Column(db.Float, nullable=True)

class OutPending(db.Model):
    __tablename__ = 'out_pending'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    amount_pending = db.Column(db.Float, nullable=False)
    last_purchase = db.Column(db.String, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class GardenLedger(db.Model):
    __tablename__ = "garden_ledger"
    id = db.Column(db.Integer, primary_key=True)
    garden_name = db.Column(db.String(100), nullable=False)
    advance_given = db.Column(db.Float, nullable=False)
    total_amount_procured = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Outbound(db.Model):
    __tablename__ = 'outbound'
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String, nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    no_of_trays = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g. "seller", "buyer", "admin"

# --------------------------
# HELPERS
# --------------------------
def parse_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default

def parse_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(float(value))
    except Exception:
        return default

def calc_quantity(weight, trays):
    """Quantity = weight - 2 * no_of_trays"""
    return weight - (2 * trays)

# --------------------------
# ROUTES
# --------------------------
# ... keep all your routes as-is ...
# (login, index, logout, auction, add_auction, available_stock, add_available_stock,
# direct_inbound, add_direct_inbound, garden_ledger, employee, add_employee,
# outpending, add_outpending, outbound, add_outbound, select_seller, seller_page, etc.)
# No changes needed here; your logic is intact.

# --------------------------
# MAIN
# --------------------------
if __name__ == '__main__':
    with app.app_context():
        # 1️⃣ Create all tables first
        db.create_all()
        print("✅ Tables created (if not already present).")

        # 2️⃣ Add default users AFTER tables are ready
        users = [
            {"username": "avallam", "password": "chennai", "role": "vallam_chennai"},
            {"username": "thoztham", "password": "kerala", "role": "kerala"},
            {"username": "allinall", "password": "ceo", "role": "ceo"},
        ]

        for u in users:
            existing = StaffUser.query.filter_by(username=u["username"]).first()
            if not existing:
                db.session.add(StaffUser(username=u["username"], password=u["password"], role=u["role"]))
        db.session.commit()
        print("✅ Default users added")

    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
