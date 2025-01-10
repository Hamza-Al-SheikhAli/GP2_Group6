#Creating data base
#We need to connect first to the db then we build our own database
import mysql.connector

#This is our connection 
mydb = mysql.connector.connect(host = 'localhost' ,user = 'root', passwd = ******** )


#cursor is an automation robot that do commands for you to the database
my_cursor = mydb.cursor() 
#creating the data base
my_cursor.execute("CREATE DATABASE users")
#checking if the database was creates succesfully 
my_cursor.execute("SHOW DATABASES")
for db in my_cursor:
    print(db)
