import random
import re
import MySQLdb
from click import password_option
from flask import Flask, flash, get_flashed_messages,make_response,redirect, render_template, request, session, url_for
import mysql.connector
import MySQLdb.cursors
import barcode
import hashlib
from barcode.writer import ImageWriter
from PIL import ImageFont
from barcode import UPCA
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key' 


connection = mysql.connector.connect(host='localhost', database='emar', user='root', password='')
cursor = connection.cursor()

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/dashboard')
def home():
    if 'name' in session:
        return render_template('index.html', name=session['name'])
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hashlib.md5(password.encode()).hexdigest()))
        record = cursor.fetchone()
        if record:
            session['name'] = record[1]
            if record[4] == 'admin':
                return redirect(url_for('home'))
            elif record[4] == 'cashier':
                return redirect(url_for('user'))
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password. Please try again.')
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        record = cursor.fetchone()
        if record:
            error = 'Email already exists!'
            return render_template('users.html', error=error)
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute("INSERT INTO users(name, email, password, role) VALUES (%s, %s, %s, %s)", (name, email, hashed_password, role))
        connection.commit()
        return redirect(url_for('users', success='Registration successful!'))
    else:
        return redirect(url_for('users'))
    
@app.route('/users')
def users():
    cursor.execute('SELECT * FROM users')
    record = cursor.fetchall()
    return render_template('users.html', users=record)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        user = request.form['id']
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        cursor.execute('UPDATE users SET name=%s, email=%s, role=%s WHERE id=%s', (name, email, role, user))
        connection.commit()
        flash('User details updated successfully', 'success')
        return redirect(url_for('users'))

    users = cursor.execute('SELECT * FROM users').fetchall()
    return render_template('users.html', users=users)

@app.route('/change_password', methods=['POST'])
def change_password():
    user_id = request.form['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    # Retrieve the user's current password from the database
    cursor.execute('SELECT password FROM users WHERE id=%s', (user_id,))
    user = cursor.fetchone()
    if user is None:
        # Handle the case where the query returned no results
        flash('User not found', 'error')
        return redirect(url_for('users'))
    current_hashed_password = user[0]

    # Check if the current password entered by the user matches the one in the database
    if not check_password_hash(current_hashed_password, current_password):
        flash('Incorrect current password. Please try again.', 'error')
        return redirect(url_for('users'))

    # Check if the new password and confirmation match
    if new_password != confirm_password:
        flash('New password and confirmation do not match. Please try again.', 'error')
        return redirect(url_for('users'))

    # Hash the new password and update the database
    hashed_password = generate_password_hash(new_password, method='sha256')
    cursor.execute('UPDATE users SET password=%s WHERE id=%s', (hashed_password, user_id))
    connection.commit()

    flash('Password updated successfully', 'success')
    return redirect(url_for('users'))

@app.route('/remove/<int:userid>', methods=['GET', 'POST'])
def remove(userid):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM users WHERE id = %s', (userid,))
    connection.commit()
    message ='User deleted!'
    return redirect(url_for('users', message=message))


@app.route('/print/<string:barcode_number>', methods=['GET'])
def print(barcode_number):
    return render_template('print-page.html', barcode_number=barcode_number)

@app.route('/insert', methods=['POST'])
def insert():
    if request.method == 'POST':
        p_name = request.form.get('p_name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        m_category = request.form.get('m_category')
        # Check if m_category is present in the request
        if m_category is None:
            flash("m_category is missing in the request")
            return redirect(url_for('product'))
        
        # generate the barcode number
        barcode_number = generate_random_number()
        # set the barcode format
        barcode_format = UPCA(barcode_number)
        # add product info to the barcode
        product_info = f"{barcode_number}\n PHP {price}.00 {p_name}"
        # configure barcode saving options
        saving_options = {
            'quiet_zone': 3.0,
            'font_size': 8,
            'text_distance': 3.0
        }
        # generate the barcode image and save it
        barcode_path = f"static/img/{barcode_number}"
        barcode_format.save(barcode_path, options=saving_options, text=product_info)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO product (p_name, price, quantity, m_category, barcode) VALUES (%s, %s, %s, %s, %s)", (p_name, price, quantity, m_category, barcode_number))
        connection.commit()
        flash("Data Inserted Successfully")
        return redirect(url_for('product'))


@app.route('/delete/<string:id_data>', methods=['GET'])
def delete(id_data):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM product WHERE id=%s", (id_data,))
    connection.commit()
    flash("Record Has Been Deleted Successfully")
    return redirect(url_for('product'))


@app.route('/update', methods=['POST', 'GET'])
def update():
    if request.method == 'POST':
        id_data = request.form['id']
        p_name = request.form['p_name']
        price = request.form['price']
        quantity = request.form['quantity']
        m_category = request.form['m_category']
        cursor = connection.cursor()
        cursor.execute("UPDATE product SET p_name=%s, price=%s, quantity=%s, m_category=%s WHERE id=%s", (p_name, price, quantity, m_category, id_data))
        connection.commit()
        flash("Data Updated Successfully")
        return redirect(url_for('product'))


# A function to generate a 12-digit random number for barcode
def generate_random_number():
    number = ""
    for i in range(12):
        number += str(random.randint(0, 9))
    return number

@app.route('/product')
def product():
    cursor.execute("SELECT * FROM product")
    data = cursor.fetchall()
    messages = get_flashed_messages()
    return render_template('product.html', product=data, messages=messages)




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)