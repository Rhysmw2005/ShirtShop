from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
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
    environmental_impact = db.Column(db.Float, nullable=True)  # New field
    extended_description = db.Column(db.Text, nullable=True)   # New field
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Shirt('{self.team_name}', '{self.price}', '{self.shirt_image}')"

migrate = Migrate(app, db)

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
            environmental_impact=6.5,  
            extended_description="This Everton team made up of the likes of Neville Southhall, Martin Keown and Andy Hinchliffe. Led by the legendary Howard Kendall with this shirt.", 
            owner_id=user1.id
        )
        shirt2 = Shirt(
            team_name="AC Milan",
            shirt_image="ac_milan.jpg",
            price=29.99,
            description="AC Milan home shirt from 2007",
            environmental_impact=4.5,  
            extended_description="During this season AC Milan played their 74th season in the first division of Italian football under the famous Carlo Ancelotti. They also won the club world cup this season.", 
            owner_id=user2.id  
        )
        shirt3 = Shirt(
            team_name="England National Team",
            shirt_image="england.jpg",
            price=29.99,
            description="England third team shirt from 1990",
            environmental_impact=8.5,  
            extended_description="The England team from this year consisted of some legendary players, most noteably. Paul Gascoigne, Gary Lineker and Peter Shilton between the sticks.", 
            owner_id=user1.id  
        )
        shirt4 = Shirt(
            team_name="Netherlands National Team",
            shirt_image="netherlands.jpg",
            price=29.99,
            description="Netherlands home shirt from 1988",
            environmental_impact=7.5,  
            extended_description="This well known shirt from the Netherlands was worn by many world renowned players such as Ronald Koeman, Frank Rijkard, Marco Van Basten and Ruud Gullit", 
            owner_id=user2.id  
        )
        shirt5 = Shirt(
            team_name="Manchester United",
            shirt_image="man_utd.jpg",
            price=29.99,
            description="Manchester United shirt from 1999",
            environmental_impact= 9.5,  
            extended_description="In our opinion this is what everyone thinks of when we mention an old United shirt. This shirt was worn by players such as Gary Neville, David Beckham, Phil Neville and Ryan Giggs", 
            owner_id=user1.id  
        )
        shirt6 = Shirt(
            team_name="Celtic",
            shirt_image="celtic.jpg",
            price=24.99,
            description="Celtic home shirt from 1997",
            environmental_impact=5.5,  
            extended_description="This shirt is a stallwart of Scottish football which was worn by the likes of Henrik Larsson and Alan Stubbs", 
            owner_id=user2.id 
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
    # Get search query and sort order from query parameters
    query = request.args.get("query", "")  # Default to an empty string if no query
    sort_order = request.args.get("sort", "asc")  # Default to ascending order
    
    # Base query for shirts
    shirt_query = Shirt.query
    
    # Apply search filter if a query is provided
    if query:
        shirt_query = shirt_query.filter(Shirt.team_name.ilike(f"%{query}%"))  # Case-insensitive search
    
    # Apply sorting based on the sort_order
    if sort_order == "asc":
        shirt_query = shirt_query.order_by(Shirt.team_name.asc())  # Ascending order
    else:
        shirt_query = shirt_query.order_by(Shirt.team_name.desc())  # Descending order
    
    shirts = shirt_query.all()  # Execute the query and get the results
    
    return render_template("home.html", shirts=shirts, sort_order=sort_order)



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