from flask import Flask , render_template ,redirect, flash , url_for,request,jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField , PasswordField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
#Importing flask framework, and render templates(html)
from flask_migrate import Migrate
from waitress import serve
import hmac
import hashlib
import time
from flask_socketio import SocketIO, emit
app = Flask(__name__) #Any app must contain an unique name, here how to give it a name  


#Database, here we connect our app with the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:hamzash079@localhost/users'

#Adding CRSF token
app.config['SECRET_KEY'] = "hello"
#Initialize the database
db =SQLAlchemy(app)
migrate = Migrate(app, db)

#Adds real-time, bidirectional communication between clients (browsers) and your Flask server
#When a client connects to the Flask server, it establishes a WebSocket connection.
socketio = SocketIO(app)
SECRET_KEY = b'Dr Mohammed alshorman is the king'


def verify_signature(payload, signature):
    computed_signature = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_signature, signature)
 
 
#The class inherits from db.Model 
#which is an instance of the SQLAlchemy declarative base class. This allows the User class to interact with a database.
class User(db.Model):
    #Every line creats a column in the database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique = True) #nullable indicates that the name column cannot be empty when creating a new User object
    value = db.Column(db.String(100), nullable=False) #Here we must put the range 
    #uwb_id= db.Column(db.String(100), nullable = False)
    password = db.Column(db.String(10000), nullable=False)
    def __repr__(self):
        return f'<User {self.name}>'
#The __repr__ method provides a human-readable representation of a User object.


#Create a Form class

#Asking for name    
class nameform(FlaskForm):
    name= StringField("Enter Your name", validators=[DataRequired()])
    submit= SubmitField("submit")

#Ask for value
class valueForm(FlaskForm):
    value = StringField("Enter a value:", validators=[DataRequired()])
    submit = SubmitField("Next")

#Ask for password
class passwordForm(FlaskForm):
    password = PasswordField("Enter your password:", validators=[DataRequired()])
    submit = SubmitField("Submit")

#This function will check the range send from the authenticator 
def perform_action(value,user_id):
    if float(value) < 70:
        update(user_id,value)
        return f"Action completed for value {value}"
    else:
        print(f"Token is too far away: {value}")
        return f"Token is too far away: {value}"

#Here it will receive a post request from the Client tag, and it will take the range and signature 
@app.route('/trigger', methods=['POST'])
def trigger_action():
    """Endpoint to receive data from the client."""
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Signature')
    if not signature or not verify_signature(payload, signature):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        value = data['value']
        user_id = data['user_id']
    except (TypeError, KeyError):
        return jsonify({"error": "Invalid request payload"}), 400

    result = perform_action(value,user_id)
    if 'Action' in result:
        return jsonify({"Alert": "Done", "result": result})
    elif 'Token' in result:
        return jsonify({"Alert": "Error", "result": result})


# Creat a route page that contain the main 
@app.route("/") #Root for our domaim
def about(): #adding a home page, where here is the main content
    return render_template("about.html") #telling the web browser what is out html file, changing the title of the page from here

@app.route('/welcome')
def welcome():
    user_name = request.args.get('name')
    return render_template('success.html', user_name=user_name)

def update(id, value):
	form = valueForm()
	value_to_update = User.query.get_or_404(id)
	if request.method == 'POST':
		value_to_update.value = value
		try:
			db.session.commit()
			flash("User Updated Successfully!")
			return render_template("update.html", value =value_to_update , form=form)
		except:
			flash("Error")
	else:
		return render_template("update.html", value =value_to_update , form=form)


####################################################################################################
#Creat a Sign-up page, accept both GET and POST  
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    step = request.args.get('step')
    
    if step == '3':  # Step 3: Password
        name = request.args.get('name')
        value = 1000  # Example: Default value, adjust as needed
        form = passwordForm()
        
        if form.validate_on_submit():
            # Hash the password using SHA256
            password_plaintext = form.password.data
            hashed_password = hashlib.sha256(password_plaintext.encode('utf-8')).hexdigest()
            # Save the user to the database with the hashed password
            new_user = User(name=name, value=value, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully!", category="success")
            return redirect(url_for('signin'))
        
        return render_template('signup.html', form=form, step='3')

    # Step 1: Collect username
    form = nameform()
    if form.validate_on_submit():
        # Check if the username already exists
        existing_user = User.query.filter_by(name=form.name.data).first()
        if existing_user:
            flash("Username already exists. Please choose a different name.", category="danger")
            return render_template('signup.html', form=form, step='1')
        
        # Redirect to Step 3 with the provided username
        return redirect(url_for('signup', step='3', name=form.name.data))
    
    # Default: Step 1
    return render_template('signup.html', form=form, step='1')
#####################################################################################################################################
#Creat a sign-in page
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.args.get('step') == '2':  # Step 2: Value
        name = request.args.get('name')
        form = valueForm()
        time.sleep(2)
        #if form.validate_on_submit():
        user = User.query.filter_by(name=name).first()
        if float(user.value) < 70:
            return redirect(url_for('signin', step='3', name=name))
        else:
            flash("Your token is out of range!!!!!",category="warning")
            return redirect(url_for('signin'))

    elif request.args.get('step') == '3':  # Step 3: Password
        name = request.args.get('name')
        form = passwordForm()
        if form.validate_on_submit():
        # Query the user by name
            user = User.query.filter_by(name=name).first()
            if user:
                # Hash the input password and compare it with the stored hash
                input_password_hashed = hashlib.sha256(form.password.data.encode('utf-8')).hexdigest()
                if user.password == input_password_hashed:
                    flash("Login successful!",category="success")
                    return redirect(url_for('welcome', name=user.name))
                else:
                    flash("Authentication failed. Invalid password.",category="danger")
            else:
                flash("Authentication failed. User not found.",category="warning")
        
            return redirect(url_for('signin'))
    
        return render_template('signin.html', form=form, step='3')

    # Step 1: Username
    form = nameform()
    #Checks if the form submission is valid, the data satisfies the defined rules, such as required fields or input formats.
    if form.validate_on_submit():
    #Queries the User table in the database to find the first record where the name field matches the submitted name (form.name.data).
        user = User.query.filter_by(name=form.name.data).first() 
        if user:
            user.value = 1000
            try:
                db.session.commit()
            except:
                flash("ERRORRRRRRR",category="warning")
            #Here it will send a message from the Webserver to all connected clients with a message "start processing"
            socketio.emit('start_processing', {'message': 'start'})
            return redirect(url_for('signin', step='2', name=form.name.data))
        else:
            flash("User not found, Please sign-up first!", category="warning")
            return redirect(url_for('signin'))
    return render_template('signin.html', form=form, step='1')

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
#Starts the application with WebSocket support.