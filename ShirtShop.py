from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm

# Create the Flask application and configure the database
app = Flask(__name__)
app.config['SECRET_KEY'] = '381131e633c853e7f6a06f0892f69ee7'  # Required for Flask sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    shirts = db.relationship('Shirt', backref='owner', lazy=True)  # Relationship to Shirt

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Define the Shirt model
class Shirt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    shirt_image = db.Column(db.String(20), nullable=False, default='default.jpg')
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User

    def __repr__(self):
        return f"Shirt('{self.team_name}', '{self.price}', '{self.shirt_image}')"

# Custom CLI command to seed the database
@app.cli.command("seed-db")
def seed_db():
    """Seed the database with initial data."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create users
        user1 = User(username="Alice", email="alice@example.com", password="password123")
        user2 = User(username="Bob", email="bob@example.com", password="password123")

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()  # Commit users first to get their IDs

        # Create shirts with proper owner_id references
        shirt1 = Shirt(
            team_name="Everton",
            shirt_image="everton.jpg",
            price=29.99,
            description="Everton home shirt from 1992",
            owner_id=user1.id  # Reference to User
        )
        shirt2 = Shirt(
            team_name="AC Milan",
            shirt_image="ac_milan.jpg",
            price=29.99,
            description="AC Milan home shirt from 2007",
            owner_id=user2.id  # Reference to User
        )
        shirt3 = Shirt(
            team_name="England National Team",
            shirt_image="england.jpg",
            price=29.99,
            description="England third team shirt from 1990",
            owner_id=user1.id  # Reference to User
        )
        shirt4 = Shirt(
            team_name="Netherlands National Team",
            shirt_image="netherlands.jpg",
            price=29.99,
            description="Netherlands home shirt from 1988",
            owner_id=user2.id  # Reference to User
        )
        shirt5 = Shirt(
            team_name="Manchester United",
            shirt_image="man_utd.jpg",
            price=29.99,
            description="Manchester United shirt from 1999",
            owner_id=user1.id  # Reference to User
        )
        shirt6 = Shirt(
            team_name="Celtic",
            shirt_image="celtic.jpg",
            price=24.99,
            description="Celtic home shirt from 1997",
            owner_id=user2.id  # Reference to User
        )

        # Add all shirts to the database session
        db.session.add(shirt1)
        db.session.add(shirt2)
        db.session.add(shirt3)
        db.session.add(shirt4)
        db.session.add(shirt5)
        db.session.add(shirt6)

        db.session.commit()  # Commit all shirts

        print("Database seeded with initial data.")

# Route to add items to the basket
@app.route("/add_to_basket/<int:shirt_id>", methods=["POST"])
def add_to_basket(shirt_id):
    # Initialize the basket in session if it doesn't exist
    if 'basket' not in session:
        session['basket'] = []  # Create an empty basket

    # Add the shirt ID to the basket
    session['basket'].append(shirt_id)

    flash("Item added to basket!", "success")
    return redirect(url_for("home"))  # Redirect after adding

def calculate_total_cost(basket_items):
    """Calculate the total cost of items in the basket."""
    total_cost = sum(item.price for item in basket_items)
    return total_cost

# Route to view the basket and its contents
@app.route("/basket")
def basket():
    if 'basket' not in session or len(session['basket']) == 0:
        return render_template("basket.html", message="Your basket is empty.")

    # Fetch the items from the database using the IDs in the session basket
    basket_items = Shirt.query.filter(Shirt.id.in_(session['basket'])).all()

    # Calculate the total cost
    total_cost = calculate_total_cost(basket_items)

    return render_template("basket.html", basket=basket_items, total_cost=total_cost)


@app.route("/remove_from_basket/<int:shirt_id>", methods=["POST"])
def remove_from_basket(shirt_id):
    if 'basket' in session and shirt_id in session['basket']:
        session['basket'].remove(shirt_id)  # Remove the specified item
        flash("Item removed from basket.", "success")  # Give feedback to the user
    else:
        flash("Item not found in basket.", "danger")

    return redirect(url_for("basket"))  # Redirect back to the basket page



# Home route to display shirts and add to the basket
@app.route("/")
@app.route("/home")
def home():
    # Retrieve the sorting order from query parameters
    sort_order = request.args.get("sort", "asc")  # Default to ascending order
    
    # Determine the query based on the sort order
    if sort_order == "asc":
        shirts = Shirt.query.order_by(Shirt.team_name.asc()).all()  # Ascending order
    else:
        shirts = Shirt.query.order_by(Shirt.team_name.desc()).all()  # Descending order
    
    return render_template("home.html", shirts=shirts, sort_order=sort_order)  # Pass the sort order


# Other routes for the application
@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f"Account successfully created for {form.username.data}!", "success")
        return redirect(url_for("home"))
    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == "admin@a.com" and form.password.data == "123":
            flash("You are now logged in", "success")
            return redirect(url_for("home"))
        else:
            flash("Login unsuccessful. Please check email and password.", "danger")
    return render_template("login.html", title="Login", form=form)

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
