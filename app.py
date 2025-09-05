# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret")

# DATABASE: use DATABASE_URL from Railway. Fallback to sqlite for local testing.
database_url = os.environ.get("DATABASE_URL", "sqlite:///local_dev.db")
# Heroku-style PG URI sometimes starts with postgres://; SQLAlchemy needs postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------
# MODELS (match your schema)
# --------------------------
class Auction(db.Model):
    __tablename__ = 'auction'
    id = db.Column(db.Integer, primary_key=True)
    seller_name = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    no_of_trays = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    buyer_name = db.Column(db.String(100), nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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


class Outbound(db.Model):
    __tablename__ = 'outbound'
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String, nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    no_of_trays = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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


# --------------------------
# ROUTES (robust: try/except + rollback)
# --------------------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------- AUCTION ----------
@app.route('/auction')
def auction():
    auctions = Auction.query.order_by(Auction.timestamp.desc()).all()
    return render_template('auction.html', auctions=auctions)


@app.route('/add_auction', methods=['POST'])
def add_auction():
    try:
        seller = request.form.get('seller', '').strip()
        product = request.form.get('product', '').strip()
        total_weight = parse_float(request.form.get('total_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = weight * no_of_trays
        sold_price_per_unit = parse_float(request.form.get('sold_price_per_unit'))
        buyer_name = request.form.get('buyer_name') or None
        bill_amount = quantity * price

        # Basic validation
        if not seller or not product:
            flash("Seller and Product are required.", "danger")
            return redirect(url_for('auction'))

        new_row = Auction(
            seller_name=request.form.get('seller_name'),
            product=request.form.get('product'),
            weight=weight,
            no_of_trays=no_of_trays,
            quantity=quantity,
            price=price,
            buyer_name=request.form.get('buyer_name'),
            bill_amount=bill_amount
        )
        db.session.add(new_row)
        db.session.commit()
        flash("Auction entry added.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding auction entry")
        flash(f"Error adding auction entry: {str(e)}", "danger")
    return redirect(url_for('auction'))


# ---------- AVAILABLE STOCK ----------
@app.route('/available_stock')
def available_stock():
    rows = AvailableStock.query.order_by(AvailableStock.timestamp.desc()).all()
    return render_template('available_stock.html', rows=rows)


@app.route('/add_available_stock', methods=['POST'])
def add_available_stock():
    try:
        product = request.form.get('product', '').strip()
        total_weight = parse_float(request.form.get('total_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = weight * no_of_trays

        if not product:
            flash("Product is required.", "danger")
            return redirect(url_for('available_stock'))

        new_row = AvailableStock(
            product=product,
            total_weight=total_weight,
            no_of_trays=no_of_trays,
            quantity=quantity
        )
        db.session.add(new_row)
        db.session.commit()
        flash("Available stock added.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding available stock")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('available_stock'))


# ---------- DIRECT INBOUND ----------
@app.route('/direct_inbound')
def direct_inbound():
    rows = DirectInbound.query.order_by(DirectInbound.timestamp.desc()).all()
    return render_template('direct_inbound.html', rows=rows)


@app.route('/add_direct_inbound', methods=['POST'])
def add_direct_inbound():
    try:
        name = request.form.get('name', '').strip()
        whole_weight = parse_float(request.form.get('whole_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = weight * no_of_trays
        seller_name = request.form.get('seller_name') or None

        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for('direct_inbound'))

        new_row = DirectInbound(
            name=name,
            whole_weight=whole_weight,
            no_of_trays=no_of_trays,
            quantity=quantity,
            seller_name=seller_name
        )
        db.session.add(new_row)
        db.session.commit()
        flash("Direct inbound added.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding direct inbound")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('direct_inbound'))


# ---------- EMPLOYEE ----------
@app.route('/employee')
def employee():
    rows = Employee.query.order_by(Employee.id.desc()).all()
    return render_template('employee.html', rows=rows)


@app.route('/add_employee', methods=['POST'])
def add_employee():
    try:
        name = request.form.get('name', '').strip()
        perday_salary = parse_float(request.form.get('perday_salary'))
        days_worked = parse_int(request.form.get('days_worked'))
        advance = parse_float(request.form.get('advance'))

        if not name:
            flash("Employee name is required.", "danger")
            return redirect(url_for('employee'))

        new_row = Employee(
            name=name,
            perday_salary=perday_salary,
            days_worked=days_worked,
            advance=advance
        )
        db.session.add(new_row)
        db.session.commit()
        flash("Employee added.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding employee")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('employee'))


# ---------- OUT PENDING ----------
@app.route('/outpending')
def outpending():
    rows = OutPending.query.order_by(OutPending.timestamp.desc()).all()
    return render_template('outpending.html', rows=rows)


@app.route('/add_outpending', methods=['POST'])
def add_outpending():
    try:
        name = request.form.get('name', '').strip()
        amount_pending = parse_float(request.form.get('amount_pending'))
        last_purchase = request.form.get('last_purchase') or None

        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for('outpending'))

        new_row = OutPending(
            name=name,
            amount_pending=amount_pending,
            last_purchase=last_purchase
        )
        db.session.add(new_row)
        db.session.commit()
        flash("Out pending entry added.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding outpending")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('outpending'))


# ---------- OUTBOUND ----------
@app.route('/outbound')
def outbound():
    rows = Outbound.query.order_by(Outbound.timestamp.desc()).all()
    return render_template('outbound.html', rows=rows)


@app.route('/add_outbound', methods=['POST'])
def add_outbound():
    try:
        product = request.form.get('product', '').strip()
        total_weight = parse_float(request.form.get('total_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = weight * no_of_trays

        if not product:
            flash("Product is required.", "danger")
            return redirect(url_for('outbound'))

        new_row = Outbound(
            product=product,
            total_weight=total_weight,
            no_of_trays=no_of_trays,
            quantity=quantity
        )
        db.session.add(new_row)
        db.session.commit()
        flash("Outbound entry added.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding outbound")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('outbound'))


# ---------- SIMPLE PAGES (render-only or small logic) ----------
@app.route('/seller_bill')
def seller_bill():
    # if you have a model for seller bills, fetch here
    return render_template('seller_bill.html')


@app.route('/vehicles')
def vehicles():
    return render_template('vehicles.html')


@app.route('/garden_ledger')
def garden_ledger():
    return render_template('garden_ledger.html')


@app.route('/open_whatsapp')
def open_whatsapp():
    return render_template('open_whatsapp.html')


# --------------------------
# Initialize DB if running locally
# --------------------------
if __name__ == '__main__':
    with app.app_context():
        # 🔑 Create tables in DB if they don't exist
        db.create_all()
        print("✅ Tables created (if not already present).")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
