from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_db_connection

app = Flask(__name__)
app.secret_key = "food_donation_secret_key_2026"


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = request.form["password"]
        role = request.form["role"]

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if user:
            flash("Email already exists.")
            cursor.close()
            connection.close()
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (full_name,email,password,phone,address,role)
            VALUES(%s,%s,%s,%s,%s,%s)
        """,
        (
            full_name,
            email,
            hashed_password,
            phone,
            address,
            role
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash("Registration Successful!")

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:

            if check_password_hash(user["password"], password):

                session["user_id"] = user["id"]
                session["name"] = user["full_name"]
                session["role"] = user["role"]

                if user["role"] == "Donor":
                    return redirect(url_for("donor_dashboard"))

                elif user["role"] == "Charity":
                    return redirect(url_for("charity_dashboard"))

                elif user["role"] == "Volunteer":
                    return redirect(url_for("volunteer_dashboard"))

                elif user["role"] == "Admin":
                    return redirect(url_for("admin_dashboard"))

        flash("Invalid Email or Password")

    return render_template("login.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ---------------- DASHBOARDS ---------------- #

@app.route("/donor")
def donor_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Donor":
        return "Access Denied", 403

    return render_template("donor_dashboard.html")

@app.route("/add-donation", methods=["GET", "POST"])
def add_donation():

    if "user_id" not in session:
        return redirect("/login")
    if session.get("role") != "Donor":
        return "Access Denied", 403

    if request.method == "POST":

        food_name = request.form["food_name"]
        quantity = request.form["quantity"]
        expiry_date = request.form["expiry_date"]
        pickup_address = request.form["pickup_address"]
        description = request.form["description"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO donations
            (donor_id, food_name, quantity, expiry_date,
             pickup_address, description)

            VALUES(%s,%s,%s,%s,%s,%s)
        """,(
            session["user_id"],
            food_name,
            quantity,
            expiry_date,
            pickup_address,
            description
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash("Food donation added successfully!")

        return redirect("/my-donations")

    return render_template("add_donation.html")

@app.route("/charity")
def charity_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Charity":
        return "Access Denied", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM donations
        WHERE status = 'Available'
        ORDER BY created_at DESC
    """)

    donations = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "charity_dashboard.html",
        donations=donations
    )


@app.route("/volunteer")
def volunteer_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Volunteer":
        return "Access Denied", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM donations
        WHERE status = 'Requested'
        ORDER BY created_at DESC
    """)

    donations = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "volunteer_dashboard.html",
        donations=donations
    )


@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM donations
        ORDER BY created_at DESC
    """)

    donations = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        donations=donations
    )

@app.route("/my-donations")
def my_donations():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Donor":
        return "Access Denied", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT *
    FROM donations
    WHERE donor_id=%s
    ORDER BY created_at DESC
    """,(session["user_id"],))

    donations = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "my_donations.html",
        donations=donations
    )

@app.route("/request-donation/<int:donation_id>")
def request_donation(donation_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Charity":
        return "Access Denied", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE donations
        SET status = 'Requested'
        WHERE id = %s
    """, (donation_id,))

    connection.commit()

    cursor.close()
    connection.close()

    flash("Donation requested successfully!")

    return redirect("/charity")

@app.route("/complete-donation/<int:donation_id>")
def complete_donation(donation_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Volunteer":
        return "Access Denied", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE donations
        SET status = 'Collected'
        WHERE id = %s
    """, (donation_id,))

    connection.commit()

    cursor.close()
    connection.close()

    flash("Donation marked as collected!")

    return redirect("/volunteer")
# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)