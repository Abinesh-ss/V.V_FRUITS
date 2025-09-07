# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db, StaffUser
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret")

users = [
    {"username": "staff", "password": "shop", "role": "vallam_chennai"},
    {"username": "staff", "password": "thoztham", "role": "kerala"},
    {"username": "ceo", "password": "allinall", "role": "ceo"},
]

for u in users:
    existing = StaffUser.query.filter_by(username=u["username"]).first()
    if not existing:
        new_user = StaffUser(username=u["username"], password=u["password"], role=u["role"])
        db.session.add(new_user)

db.session.commit()
print("✅ Users added")

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
    password = db.Column(db.String(100), nullable=False)  # store hashed in production
    role = db.Column(db.String(50), nullable=False)       # vallam_chennai / kerala / ceo



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
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = StaffUser.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("index"))
        else:
            flash("Invalid login. Try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    role = session.get("role")
    options = []

    if role == "vallam_chennai":
        options = ["Direct Inbound", "Auction", "Available Stock", "Out Pending"]
    elif role == "kerala":
        options = ["Garden Ledger", "Outbound", "Vehicles"]
    elif role == "ceo":
        options = ["Direct Inbound", "Auction", "Available Stock", "Out Pending",
                   "Garden Ledger", "Outbound", "Vehicles", "Employees", "Reports"]

    return render_template("index.html", options=options, role=role)


# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- AUCTION ----------
@app.route('/auction')
def auction():
    auctions = Auction.query.order_by(Auction.timestamp.desc()).all()
    return render_template('auction.html', auctions=auctions)


@app.route('/add_auction', methods=['POST'])
def add_auction():
    try:
        seller_name = request.form.get('seller_name', '').strip()
        product = request.form.get('product', '').strip()
        weight = parse_float(request.form.get('weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = calc_quantity(weight, no_of_trays)
        price = parse_float(request.form.get('price'))
        buyer_name = request.form.get('buyer_name', '').strip()
        bill_amount = quantity * price

        if not seller_name or not product:
            flash("Seller and Product are required.", "danger")
            return redirect(url_for('auction'))

        new_row = Auction(
            seller_name=seller_name,
            product=product,
            weight=weight,
            no_of_trays=no_of_trays,
            quantity=quantity,
            price=price,
            buyer_name=buyer_name,
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
        weight = parse_float(request.form.get('total_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = calc_quantity(weight, no_of_trays)

        if not product:
            flash("Product is required.", "danger")
            return redirect(url_for('available_stock'))

        new_row = AvailableStock(
            product=product,
            total_weight=weight,
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
        weight = parse_float(request.form.get('whole_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = calc_quantity(weight, no_of_trays)
        seller_name = request.form.get('seller_name', '').strip()

        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for('direct_inbound'))

        new_row = DirectInbound(
            name=name,
            whole_weight=weight,
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


# ---------- GARDEN LEDGER ----------
@app.route('/garden_ledger')
@app.route("/garden_ledger", methods=["GET", "POST"])
def garden_ledger():
    if request.method == "POST":
        garden_name = request.form["garden_name"]
        advance_given = float(request.form["advance_given"])
        total_amount_procured = float(request.form["total_amount_procured"])

        new_entry = GardenLedger(
            garden_name=garden_name,
            advance_given=advance_given,
            total_amount_procured=total_amount_procured,
        )
        db.session.add(new_entry)
        db.session.commit()
        flash("Garden Ledger entry added!", "success")
        return redirect(url_for("garden_ledger"))

    # Sorting option
    sort = request.args.get("sort", "timestamp")  # default sort by timestamp
    if sort == "garden_name":
        rows = GardenLedger.query.order_by(GardenLedger.garden_name).all()
    else:
        rows = GardenLedger.query.order_by(GardenLedger.timestamp.desc()).all()

    return render_template("garden_ledger.html", rows=rows, sort=sort)


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
        weight = parse_float(request.form.get('total_weight'))
        no_of_trays = parse_int(request.form.get('no_of_trays'))
        quantity = calc_quantity(weight, no_of_trays)

        if not product:
            flash("Product is required.", "danger")
            return redirect(url_for('outbound'))

        new_row = Outbound(
            product=product,
            total_weight=weight,
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

@app.route("/select_seller", methods=["GET", "POST"])
def select_seller():
    if request.method == "POST":
        seller_name = request.form.get("seller")
        return redirect(url_for("seller_page", seller=seller_name))
    return render_template("select_seller.html")


# Step 2: Multi-product invoice for seller
@app.route("/seller/<seller>", methods=["GET", "POST"])
def seller_page(seller):
    if request.method == "POST":
        product = request.form.get("product")
        total_weight = float(request.form.get("total_weight"))
        no_of_trays = int(request.form.get("no_of_trays"))
        sold_price_per_unit = float(request.form.get("sold_price_per_unit"))
        buyer_name = request.form.get("buyer_name") or None

        entry = Auction(
            seller=seller,
            product=product,
            total_weight=total_weight,
            no_of_trays=no_of_trays,
            sold_price_per_unit=sold_price_per_unit,
            buyer_name=buyer_name
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for("seller_page", seller=seller))

    # get all products for this seller
    auctions = Auction.query.filter_by(seller=seller).all()
    total_bill = sum((a.total_weight - 2*a.no_of_trays) * a.sold_price_per_unit for a in auctions)
    discounted_bill = total_bill * 0.9
    return render_template("seller_page.html", seller=seller, auctions=auctions,
                           total_bill=total_bill, discounted_bill=discounted_bill)


# ---------- SIMPLE PAGES ----------
@app.route('/seller_bill')
def seller_bill():
    return render_template('seller_bill.html')


@app.route('/vehicles')
def vehicles():
    return render_template('vehicles.html')


@app.route('/open_whatsapp')
def open_whatsapp():
    return render_template('open_whatsapp.html')


# --------------------------
# Initialize DB
# --------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Tables created (if not already present).")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
