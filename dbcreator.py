#From here we create a table in the database 
#
from server import app, db  

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
