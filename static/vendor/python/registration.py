import mysql.connector
from mysql.connector import Error

username = input("Enter username: " )
password = input("Enter password: ")
name = input("Enter First and Last Name: ")
usertype = input ("Enter 1 = Inventory or 2 = Sales: ")

try:
    con = mysql.connector.connect(host='localhost', database='em-ar', user='root', password='')
    query = "Insert INTO users (USERNAME, PASSWORD, NAME, USERTYPE) VALUES ('" + username + "', '" + password +"', + '" + name + "', '" + usertype + "' )"
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    cur.close()
except Error as error:
    print ("Insert data failed {}".format(error))
finally:
    if con.is_connected():
        con.close()
        print ("MySQL Connection is now CLOSED!")