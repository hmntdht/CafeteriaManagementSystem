from flask import Flask, render_template, request, redirect, url_for, session, flash , jsonify
from werkzeug.security import generate_password_hash , check_password_hash
import random
import os
from decimal import Decimal
from werkzeug.utils import secure_filename
from models import db, User , Order , OrderItem , Category , Payment , MenuItem ,Discount ,Khata
from flask_mail import Mail, Message
from config import Config 
from sqlalchemy import func , desc
from datetime import date, timedelta, datetime


app = Flask(__name__)
app.config.from_object(Config)  
mail = Mail(app)
db.init_app(app)
with app.app_context():
    db.create_all() 

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# #creating admin
# with app.app_context():
#     admin = User(
#         name="Admin",
#         email="admin@canteen.com",
#         password=generate_password_hash("admin123"),
#         role="admin"
#     )
#     db.session.add(admin)
#     db.session.commit()
# with app.app_context():
#     default_categories = [
#         {"id": 101, "name": "Breakfast"},
#         {"id": 102, "name": "Lunch"},
#         {"id": 103, "name": "Beverage"}
#     ]

#     for cat in default_categories:
#         if not Category.query.get(cat["id"]):
#             db.session.add(Category(id=cat["id"], name=cat["name"]))

#     db.session.commit()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        # Basic server-side validation
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("signup"))

        # Check if email already exists in DB
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists.", "danger")
            return redirect(url_for("login"))

        # Generate OTP
        otp = random.randint(100000, 999999)

        # Save temporary user data in session
        session["temp_user"] = {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "otp": otp
        }

        # Send OTP email
        try:
            msg = Message(
                subject="Your OTP for Nast Eat Signup",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email],
                body=f"Hello {name},\n\nYour OTP is: {otp}\n\nDo not share this with anyone."
            )
            mail.send(msg)
            flash("OTP sent to your email! Please verify.", "success")
            return redirect(url_for("verify_otp"))

        except Exception as e:
            flash(f"Error sending email: {str(e)}", "danger")
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    temp_user = session.get("temp_user")
    if not temp_user:
        flash("Session expired. Please signup again.", "danger")
        return redirect(url_for("signup"))

    if request.method == "POST":
        entered_otp = request.form.get("otp")
        if str(entered_otp) == str(temp_user["otp"]):
            # Save user to database
            new_user = User(
                name=temp_user["name"],
                email=temp_user["email"],
                password=temp_user["password"]
            )
            db.session.add(new_user)
            db.session.commit()

            session.pop("temp_user")
            flash("Signup successful! You can now login.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid OTP. Try again.", "danger")
    
    return render_template(
        "verify_otp.html",
        email=temp_user["email"],
        next_url=url_for("verify_otp")
    )

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email").strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not found.", "danger")
            return redirect(url_for("forgot_password"))

        # Generate OTP and save to session
        otp = random.randint(100000, 999999)
        session["reset_user"] = {"email": email, "otp": otp}

        # Send OTP email
        try:
            msg = Message(
                subject="Your OTP to Reset Password",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email],
                body=f"Hello {user.name},\n\nYour OTP for password reset is: {otp}\n\nDo not share this with anyone."
            )
            mail.send(msg)
            flash("OTP sent to your email! Please verify.", "success")
            return redirect(url_for("reset_password_verify"))

        except Exception as e:
            flash(f"Error sending email: {str(e)}", "danger")
            return redirect(url_for("forgot_password"))

    # GET request → just render the form
    return render_template("forgot_password.html")


# ---------------- RESET PASSWORD OTP VERIFICATION ----------------
@app.route("/reset-password-verify", methods=["GET", "POST"])
def reset_password_verify():
    reset_user = session.get("reset_user")
    if not reset_user:
        flash("Session expired or invalid. Please try again.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        entered_otp = request.form.get("otp")
        if str(entered_otp) == str(reset_user["otp"]):
            flash("OTP verified! You can now reset your password.", "success")
            return redirect(url_for("reset_password_form"))
        else:
            flash("Invalid OTP. Try again.", "danger")

    # Render dynamic OTP template
    return render_template(
        "verify_otp.html",
        email=reset_user["email"],
        next_url=url_for("reset_password_verify")
    )


# ---------------- RESET PASSWORD FORM ----------------
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password_form():
    reset_user = session.get("reset_user")
    if not reset_user:
        flash("Session expired or invalid. Please try again.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if not password or not confirm_password:
            flash("Please fill all fields.", "danger")
            return redirect(url_for("reset_password_form"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("reset_password_form"))
        
        if len(password)<6 :
            flash("Password must be greater than 6 character" , "danger")
            return redirect(url_for("reset_password_form"))

        # Update password in database
        user = User.query.filter_by(email=reset_user["email"]).first()
        user.password = generate_password_hash(password)
        db.session.commit()

        # Remove session data
        session.pop("reset_user")
        flash("Password reset successful! You can now login.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    menu_items = MenuItem.query.filter_by(availability=True).all()
    return render_template("dashboard.html", menu_items=menu_items)


#login 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Query the user
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User not found. Please check your email.", "danger")
            return redirect(url_for("login"))

        #checking for banned 
        if user.is_banned:
            flash("Your account has been banned. Contact admin.", "danger")
            return redirect(url_for("login"))

        if user and check_password_hash(user.password, password):
            # Successful login
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Logged in successfully!", "success")
            if user.role == "admin":
                return redirect(url_for("admin_panel"))  # Your admin panel route
            else:
                return redirect(url_for("dashboard"))  # Normal customer panel
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")


    
# ---------------- CATEGORY ----------------
@app.route("/category")
def category():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    categories = Category.query.all()
    return render_template("category.html", categories=categories)

# ---------------- ORDER ITEMS ----------------
@app.route("/order_items")
def order_items():
    order = session.get("current_order", [])
    total = sum(item["price"] * item["quantity"] for item in order)

    # Initialize discount session variables if they don't exist
    if "discount_applied" not in session:
        session["discount_applied"] = False
        session["discount_amount"] = 0
        session["discount_code"] = ""
        session["discount_percentage"] = 0

    discount_applied = session.get("discount_applied")
    discount_amount = session.get("discount_amount", 0)
    total_after_discount = total - discount_amount if discount_applied else total

    return render_template(
        "order_items.html",
        order=order,
        total=total,
        total_after_discount=total_after_discount,
        discount_applied=discount_applied,
        discount_amount=discount_amount
    )



# ---------------- UPDATE ORDER QUANTITY ----------------
@app.route("/update_order")
def update_order():
    item_name = request.args.get("item_name")
    change = int(request.args.get("change", 0))
    order = session.get("current_order", [])

    for item in order:
        if item["name"] == item_name:
            item["quantity"] += change
            # prevent negative or zero quantity
            if item["quantity"] <= 0:
                order.remove(item)
            break

    session["current_order"] = order
    return redirect(url_for("order_items"))


# ---------------- ADD ITEM TO ORDER ----------------
@app.route("/add_to_order")
def add_to_order():
    item_name = request.args.get('item')
    price = float(request.args.get('price'))
    order = session.get('current_order', [])

    for i, item in enumerate(order):
        if item['name'] == item_name:
            item['quantity'] += 1
            break
    else:
        order.append({'name': item_name, 'price': price, 'quantity': 1})

    session['current_order'] = order
    flash(f"{item_name} has been added to your Order Items.", "info")
    return redirect(request.referrer or url_for("dashboard"))


#discount creator 
@app.route('/admin/create_discount', methods=['POST'])
def create_discount():
    # Delete expired discounts
    Discount.query.filter(Discount.end_time <= datetime.now()).delete()
    db.session.commit()

    code = request.form.get('code').strip()

    # Validate amount
    try:
        amount = float(request.form.get('amount'))
    except ValueError:
        flash("Invalid percentage value.", "danger")
        return redirect(url_for('admin_panel'))

    if amount <= 0 or amount > 100:
        flash("Discount percentage must be between 0 and 100.", "danger")
        return redirect(url_for('admin_panel'))

    # Parse start and end times
    try:
        start_time = datetime.fromisoformat(request.form.get('start_time'))
        end_time = datetime.fromisoformat(request.form.get('end_time'))
    except ValueError:
        flash("Invalid date/time format.", "danger")
        return redirect(url_for('admin_panel'))

    if start_time >= end_time:
        flash("End time must be after start time.", "danger")
        return redirect(url_for('admin_panel'))

    # Check if coupon already exists
    if Discount.query.filter_by(code=code).first():
        flash("Coupon code already exists.", "danger")
        return redirect(url_for('admin_panel'))

    # Create and commit the new coupon
    new_discount = Discount(
        code=code,
        amount=amount,
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(new_discount)
    db.session.commit()

    flash("Coupon created successfully!", "success")
    return redirect(url_for('admin_panel'))

#apply discount 
@app.route("/apply_discount", methods=["POST"])
def apply_discount():
    discount_code = request.form.get("discount_code", "").strip()
    discount = Discount.query.filter_by(code=discount_code).first()

    if not discount:
        flash("Invalid discount code.", "danger")
        return redirect(url_for("order_items"))

    now = datetime.now()
    if not (discount.start_time <= now <= discount.end_time):
        flash("This coupon is not currently valid.", "danger")
        return redirect(url_for("order_items"))

    # Cart is in session
    order = session.get("current_order", [])
    if not order:
        flash("No items in your current order.", "danger")
        return redirect(url_for("order_items"))

    total = sum(item["price"] * item["quantity"] for item in order)

    # If your Discount.amount is percentage
    discount_amount = total * (float(discount.amount) / 100)
    discounted_total = max(total - discount_amount, 0)

    # Save discount info in session only
    session["discount_applied"] = True
    session["discount_amount"] = discount_amount
    session["discount_code"] = discount.code
    session["discount_percentage"] = float(discount.amount)
    session["discounted_total"] = discounted_total

    flash(f"Discount applied! You saved Rs. {discount_amount:.2f} ({discount.amount}% off).", "success")
    return redirect(url_for("order_items"))


# ---------------- CHECKOUT ----------------
@app.route("/checkout", methods=["POST", "GET"])
def checkout():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    # Get current order from session
    order_items_session = session.get('current_order', [])
    if not order_items_session:
        flash("Your order is empty.", "danger")
        return redirect(url_for('order_items'))

    # Calculate totals
    total_original = sum(item.get('price', 0) * item.get('quantity', 0) for item in order_items_session)
    discount_amount = session.get('discount_amount', 0) if session.get('discount_applied') else 0
    total_discounted = total_original - discount_amount

    # Create new Order
    new_order = Order(
        user_id=session['user_id'],
        total_amount=total_discounted,
        status='Pending'
    )
    db.session.add(new_order)
    db.session.commit()  

    # Save order items
    for item in order_items_session:
        menu_item = MenuItem.query.filter_by(name=item.get('name')).first()
        if menu_item:
            order_item = OrderItem(
                order_id=new_order.id,
                item_id=menu_item.id,
                quantity=item.get('quantity', 0),
                rate=item.get('price', 0)
            )
            db.session.add(order_item)
    db.session.commit()

    # Create Payment record
    new_payment = Payment(
        order_id=new_order.id,
        payment_status='Pending',
        paid_amount=total_discounted,
        discount=discount_amount,
        total_amount=total_original,
        discount_code=session.get('discount_code')
    )
    db.session.add(new_payment)
    db.session.commit()

    # Clear session cart + discount info
    for key in ['current_order', 'discount_applied', 'discount_amount', 'discount_code', 'discount_percentage']:
        session.pop(key, None)

    # Get customer name
    user = User.query.get(session['user_id'])
    customer_name = user.name if user else "Customer"

    # Render waiting page
    return render_template("order_wait.html", customer_name=customer_name)


# ---------------- ORDER STATUS API ----------------
@app.route("/order_status/<int:user_id>")
def order_status(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"order": None})

    # Get latest order
    latest_order = (
        Order.query.filter_by(user_id=user_id)
        .order_by(Order.order_date.desc())
        .first()
    )
    if not latest_order:
        return jsonify({"order": None})

    # Get payment info
    payment = Payment.query.filter_by(order_id=latest_order.id).first()
    discount_amount = float(payment.discount) if payment else 0

    # Prepare items and total
    order_items = [oi for oi in latest_order.order_items if oi.menu_item]
    total_original = sum(float(oi.rate) * oi.quantity for oi in order_items)

    items_list = []
    for oi in order_items:
        price = float(oi.rate)
        quantity = oi.quantity

        if total_original > 0 and discount_amount > 0:
            # Calculate proportional discount per item
            proportion = (price * quantity) / total_original
            discounted_price = price - (discount_amount * proportion / quantity)
        else:
            discounted_price = price

        items_list.append({
            "name": oi.menu_item.name,
            "quantity": quantity,
            "price": round(price, 2),
            "discounted_price": round(discounted_price, 2)
        })

    # Total discounted amount
    total_discounted = total_original - discount_amount if discount_amount > 0 else total_original

    response = {
        "order_id": latest_order.id,
        "order_datetime": latest_order.order_date.strftime("%Y-%m-%d %H:%M"),
        "items": items_list,
        "total_original": round(total_original, 2),
        "total_discounted": round(total_discounted, 2),
        "status": latest_order.status
    }

    return jsonify({"order": response})



#admin orders 
@app.route("/admin/orders")
def admin_orders():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user or user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login"))

    return render_template("admin_orders.html")

@app.route("/admin/orders_json")
def admin_orders_json():
    orders = (
        db.session.query(Order, Payment, User)
        .join(Payment, Payment.order_id == Order.id)
        .join(User, User.id == Order.user_id)
        .order_by(Order.order_date.desc())
        .all()
    )

    orders_list = []

    for order, payment, user in orders:
        # Prepare items with original and discounted prices
        order_items_list = []
        for item in order.order_items:
            menu_item = MenuItem.query.get(item.item_id)

            # Ensure all values are floats
            item_rate = float(item.rate)
            quantity = float(item.quantity)
            total_amount = float(payment.total_amount)
            paid_amount = float(payment.paid_amount)
            discount = float(payment.discount) if payment.discount else 0.0

            # Calculate per-item discounted price proportionally
            if discount > 0 and total_amount > 0:
                proportion = (item_rate * quantity) / total_amount
                discounted_amount = paid_amount * proportion / quantity
            else:
                discounted_amount = item_rate

            order_items_list.append({
                "name": menu_item.name,
                "quantity": int(item.quantity),  # keep quantity as integer
                "price": round(item_rate, 2),
                "price_discounted": round(discounted_amount, 2)
            })

        orders_list.append({
            "order_id": order.id,
            "customer_name": user.name,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M"),
            "status": order.status,
            "total_original": round(float(payment.total_amount), 2),
            "total_discounted": round(float(payment.paid_amount), 2),
            "items": order_items_list,
            "discount": round(float(payment.discount) if payment.discount else 0.0, 2),
            "discount_code": payment.discount_code
        })

    return jsonify({"orders": orders_list})



#approve order 
@app.route("/admin/approve_order/<int:order_id>")
def approve_order(order_id):
    order = Order.query.get(order_id)
    if order and order.status == "Pending":
        order.status = "Accepted"
        db.session.commit()
        return {"success": True}
    return {"success": False}, 400


# Reject order
@app.route("/admin/reject_order/<int:order_id>")
def reject_order(order_id):
    order = Order.query.get(order_id)
    if order and order.status in ["Pending", "Accepted"]:
        order.status = "Rejected"
        db.session.commit()
        return {"success": True}
    return {"success": False}, 400


# Mark order as Paid
@app.route("/admin/pay_order/<int:order_id>")
def pay_order(order_id):
    order = Order.query.get(order_id)
    if order and order.status in ["Accepted", "Pending"]:
        order.status = "Paid"
        db.session.commit()

        # Send email to user
        user = order.user
        total_amount = float(order.total_amount)

        try:
            msg = Message(
                subject=f"Payment Received - Order #{order.id}",
                recipients=[user.email],
                body=f"""
Hello {user.name},

We hope you enjoyed your visit at Nast Eat!  

This is a confirmation that your payment of Rs. {total_amount:.2f} for Order #{order.id} has been successfully received.  

Thank you for choosing us. We look forward to serving you again soon!

Best regards,
Nast Eat Team
"""
            )
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

        return {"success": True}

    return {"success": False}, 400

# Add order to Khata
@app.route("/admin/khata_order/<int:order_id>")
def khata_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return {"success": False, "message": "Order not found"}, 404

    # Only allow Khata update for Accepted or Pending orders
    if order.status not in ["Accepted", "Pending"]:
        return {"success": False, "message": "Order cannot be added to Khata"}, 400

    # Update order status
    order.status = "Khata"
    order_amount = Decimal(str(order.total_amount))

    # Create a new Khata record for this order
    khata_record = Khata(
        user_id=order.user_id,
        order_id=order.id,
        amount=order_amount
    )
    db.session.add(khata_record)
    db.session.commit()  # Commit new Khata entry

    # Fetch updated total Khata for the user
    total_khata = db.session.query(func.sum(Khata.amount))\
                            .filter_by(user_id=order.user_id).scalar()
    total_khata = float(total_khata) if total_khata else 0.0

    # Send email notification
    user = order.user  # Assuming Order model has relationship to User
    try:
        msg = Message(
            subject=f"Khata Updated - Rs. {order_amount:.2f} Added",
            recipients=[user.email],
            body=f"""
Hello {user.name},

We hope you are enjoying your experience at Nast Eat!

Rs. {order_amount:.2f} has been added to your Khata account following your recent order (Order #{order.id}).  

Your current Khata balance is now Rs. {total_khata:.2f}.  

You can settle your Khata at any time at the counter. We greatly appreciate your continued patronage and thank you for trusting Nast Eat.

Warm regards,
Nast Eat Team
"""
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

    return {"success": True, "khata_total": total_khata}


#---------------- History---------------- 
@app.route('/history')
def history():
    filter_period = request.args.get('filter', 'all')    # All / week / month / 6month
    filter_status = request.args.get('status', 'all')    # All / Paid / Khata
    user_id = session["user_id"]

      # Base query: only Paid or Khata
    orders_query = Order.query.filter(
        Order.user_id == user_id,
        Order.status.in_(['Paid', 'Khata'])
    )
    # Time filter
    now = datetime.now()
    if filter_period == 'week':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(weeks=1))
    elif filter_period == 'month':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(days=30))
    elif filter_period == '6month':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(days=180))

    # Status filter
    if filter_status != 'all':
        orders_query = orders_query.filter(Order.status == filter_status)

    # Order by date descending
    orders = orders_query.order_by(Order.order_date.desc()).all()

    return render_template(
        'history.html',
        orders=orders,
        filter_period=filter_period,
        filter_status=filter_status
    )

# ---------------- ACCOUNT ----------------
@app.route("/account", methods=["GET", "POST"])
def account():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    total_khata = db.session.query(func.sum(Khata.amount))\
                            .filter_by(user_id=user.id).scalar()
    
    # Ensure a number (float) is passed to template
    khata_amount = float(total_khata) if total_khata else 0.0

    if request.method == "POST":
        # handle feedback submission
        feedback = request.form.get("feedback")
        if feedback:
            # save feedback in DB if table exists, or print/log
            flash("Feedback submitted. Thank you!", "success")
        return redirect(url_for("account"))

    
    return render_template("account.html", user=user, khata_amount=khata_amount)


@app.route("/admin/dashboard")
def admin_panel():
    # --- Check if user is logged in ---
    if "user_id" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user or user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login"))

    #discount coupon showing 
    # Fetch totals 
    totals = db.session.query(
        func.coalesce(func.sum(Payment.total_amount), 0).label("gross_total"),
        func.coalesce(func.sum(Payment.paid_amount), 0).label("net_total")
    ).first()

    # Get only active coupons
    now = datetime.now()
    active_coupons = Discount.query.filter(
        Discount.start_time <= now,
        Discount.end_time >= now
    ).all()

    # --- Dashboard stats ---
    today = date.today()
    orders_today = Order.query.filter(
        Order.order_date >= datetime.combine(today, datetime.min.time()),
        Order.order_date <= datetime.combine(today, datetime.max.time())
    ).count()

    seven_days_ago = datetime.now() - timedelta(days=7)
    orders_week = Order.query.filter(Order.order_date >= seven_days_ago).count()

    # Best-selling item
    best_item = db.session.query(
        MenuItem.name,
        func.count(OrderItem.id).label("count")
    ).join(OrderItem, OrderItem.item_id == MenuItem.id)\
     .group_by(MenuItem.id)\
     .order_by(desc("count"))\
     .first()

    best_item_name = best_item[0] if best_item else "N/A"

    # Total customers
    logged_users = User.query.filter_by(role="customer").count()

    # All items and users
    items = MenuItem.query.all()
    users = User.query.all()

    # --- Daily sales (last 7 days) ---
    daily_sales = db.session.query(
        func.date(Order.order_date).label("day"),
        func.coalesce(func.sum(Payment.total_amount), 0).label("total")
    ).join(Payment, Payment.order_id == Order.id)\
     .filter(Order.order_date >= seven_days_ago)\
     .group_by("day")\
     .order_by("day").all()

    daily_labels = [str(row.day) for row in daily_sales]
    daily_totals = [float(row.total) for row in daily_sales]

        # --- Monthly sales (last 6 months) ---
    six_months_ago = datetime.now() - timedelta(days=30*6)
    monthly_sales = db.session.query(
        func.date_format(Order.order_date, "%Y-%m").label("month"),
        func.coalesce(func.sum(Payment.total_amount), 0).label("total")
    ).join(Payment, Payment.order_id == Order.id)\
    .filter(Order.order_date >= six_months_ago)\
    .group_by("month")\
    .order_by("month").all()

    monthly_labels = [row.month for row in monthly_sales]
    monthly_totals = [float(row.total) for row in monthly_sales]

     # Categories for the "Add Item" form dropdown
    categories = Category.query.all()

    return render_template(
        "admin_panel.html",
        orders_today=orders_today,
        orders_week=orders_week,
        best_item=best_item_name,
        logged_users=logged_users,
        items=items,
        users=users,
        categories=categories,
        daily_labels=daily_labels,
        daily_totals=daily_totals,
        monthly_labels=monthly_labels,
        monthly_totals=monthly_totals,
        gross_total=totals.gross_total,
        net_total=totals.net_total,
        coupons=active_coupons,
        now=now
    )

@app.route("/ban_user/<int:user_id>")
def ban_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_banned = True
        db.session.commit()
        flash(f"{user.name} has been banned.", "success")
    else:
        flash("User not found.", "danger")
    return redirect(url_for("admin_panel"))

@app.route("/unban_user/<int:user_id>")
def unban_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_banned = False
        db.session.commit()
        flash(f"{user.name} has been unbanned.", "success")
    else:
        flash("User not found.", "danger")
    return redirect(url_for("admin_panel"))


#make available and unavailable 
@app.route("/toggle_item/<int:item_id>")
def toggle_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.availability = not item.availability
    db.session.commit()
    flash(f"'{item.name}' availability updated!", "success")
    return redirect(url_for("admin_panel"))

@app.route("/add_item", methods=["POST"])
def add_item():
    name = request.form["name"]
    price = request.form["price"]
    category_id = request.form["category"]   # comes as string from form
    image_file = request.files.get("image")

    filename = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)
        filename = f"uploads/{filename}"

    new_item = MenuItem(
        name=name,
        price=price,
        category_id=int(category_id),   # ✅ use category_id
        availability=True,              # ✅ correct field name
        image_url=filename
    )
    db.session.add(new_item)
    db.session.commit()

    flash("Menu item added successfully!", "success")
    return redirect(url_for("admin_panel"))


# Show feedback form
@app.route('/feedback')
def feedback_form():
    return render_template('feedback.html')

# Handle feedback submission
@app.route('/send_feedback', methods=['POST'])
def send_feedback():
    name = request.form.get('name')
    user_email = request.form.get('email')  # email entered by user
    message_body = request.form.get('message')

    # 📩 Feedback email → goes to ADMIN (you)
    msg_to_admin = Message(
        subject=f"New Feedback from {name}",
        recipients=['nasteat31@gmail.com'],  # admin email
        body=f"Name: {name}\nEmail: {user_email}\nMessage:\n{message_body}"
    )

    # 📩 Auto-reply → goes to USER
    auto_reply = Message(
        subject="Thank you for your feedback!",
        recipients=[user_email],  # user email from form
        body=f"""
            Hello {name},
            Thank you for your feedback! We have received your 
            message.
            Here’s a copy of your feedback:
            --------------------------------
            {message_body}
            --------------------------------

            We appreciate you taking the time to help us improve.

            Best regards,  
            Nast Eat Team
            """
                )

    try:
        mail.send(msg_to_admin)  # send feedback to admin
        mail.send(auto_reply)    # send thank-you note to user  
        flash("Feedback sent successfully!", "success")
    except Exception as e:
        print(" Error sending email:",e)
        flash("Failed to send feedback.", "danger")

    return redirect(url_for('feedback_form'))

#Khata settilement 

@app.route("/admin/khata")
def admin_khata():
    search_query = request.args.get('search', '')

    # Subquery: sum khata amount for each user
    khata_subquery = db.session.query(
        Khata.user_id,
        func.coalesce(func.sum(Khata.amount), 0).label('total_khata')
    ).group_by(Khata.user_id).subquery()

    # Join with user to get names and emails
    query = db.session.query(User, khata_subquery.c.total_khata).join(
        khata_subquery, User.id == khata_subquery.c.user_id
    )

    if search_query:
        query = query.filter(User.name.ilike(f"%{search_query}%"))

    users = query.order_by(khata_subquery.c.total_khata.desc()).all()

    return render_template("admin_khata.html", users=users, search_query=search_query)


@app.route("/admin/khata/settle/<int:user_id>", methods=["POST"])
def settle_khata(user_id):
    user = User.query.get_or_404(user_id)

    try:
        payment_amount = float(request.form.get('payment_amount', 0))
    except ValueError:
        flash("Invalid amount entered.", "danger")
        return redirect(url_for('admin_khata'))

    if payment_amount <= 0:
        flash("Amount must be greater than 0.", "danger")
        return redirect(url_for('admin_khata'))

    # Calculate current Khata
    total_khata = db.session.query(db.func.coalesce(db.func.sum(Khata.amount), 0))\
                    .filter(Khata.user_id == user.id).scalar()
    total_khata_float = float(total_khata)

    if payment_amount > total_khata_float:
        flash("Payment exceeds current Khata balance.", "danger")
        return redirect(url_for('admin_khata'))

    # --- Create or get dummy settlement order ---
    dummy_order = Order.query.filter_by(user_id=user.id, status="Settlement").first()
    if not dummy_order:
        dummy_order = Order(
            user_id=user.id,
            total_amount=0,
            status="Settlement",
            order_date=datetime.utcnow()
        )
        db.session.add(dummy_order)
        db.session.commit()  # commit to generate order.id

    # --- Add negative Khata record linked to dummy order ---
    new_record = Khata(
        user_id=user.id,
        order_id=dummy_order.id,
        amount=-payment_amount,
        created_at=datetime.utcnow()
    )
    db.session.add(new_record)
    db.session.commit()

    # --- Send email ---
    remaining_balance = total_khata_float - payment_amount
    msg = Message(
        subject="Khata Settlement Confirmation",
        recipients=[user.email],
        body=f"Dear {user.name},\n\n"
             f"You have successfully paid Rs.{payment_amount:.2f} towards your Khata. "
             f"Your remaining Khata balance is Rs.{remaining_balance:.2f}.\n\n"
             "Thank you for settling your account.\n\nBest regards,\nNast Eat"
    )
    mail.send(msg)

    flash(f"Khata updated for {user.name}", "success")
    return redirect(url_for('admin_khata'))


# Main admin history page
@app.route('/admin/history')
def admin_history():
    filter_period = request.args.get('filter_period', 'all')
    filter_status = request.args.get('filter_status', 'all')
    filter_username = request.args.get('username', '').strip()

    # Base query: all users
    orders_query = Order.query.join(User)

    # Filter by status
    if filter_status == 'Paid':
        orders_query = orders_query.filter(Order.status == 'Paid')
    elif filter_status == 'Khata':
        orders_query = orders_query.filter(Order.status == 'Khata')
    # else: show all statuses

    # Filter by username
    if filter_username:
        orders_query = orders_query.filter(User.name.ilike(f'%{filter_username}%'))

    # Time filter
    now = datetime.utcnow()
    if filter_period == 'week':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(weeks=1))
    elif filter_period == 'month':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(days=30))
    elif filter_period == '6month':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(days=180))

    orders = orders_query.order_by(Order.order_date.desc()).all()

    return render_template(
        'admin_history.html',
        orders=orders,
        filter_period=filter_period,
        filter_status=filter_status,
        filter_username=filter_username
    )


# AJAX route for live filtering
@app.route('/admin/history/search')
def admin_history_search():
    filter_period = request.args.get('filter_period', 'all')
    filter_status = request.args.get('filter_status', 'all')
    filter_username = request.args.get('username', '').strip()

    orders_query = Order.query.join(User)

    if filter_status == 'Paid':
        orders_query = orders_query.filter(Order.status == 'Paid')
    elif filter_status == 'Khata':
        orders_query = orders_query.filter(Order.status == 'Khata')

    if filter_username:
        orders_query = orders_query.filter(User.name.ilike(f'%{filter_username}%'))

    now = datetime.utcnow()
    if filter_period == 'week':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(weeks=1))
    elif filter_period == 'month':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(days=30))
    elif filter_period == '6month':
        orders_query = orders_query.filter(Order.order_date >= now - timedelta(days=180))

    orders = orders_query.order_by(Order.order_date.desc()).all()
    return render_template('admin_history_list.html', orders=orders)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__": 
    app.run(debug=True)
