import random
import re
import MySQLdb
from flask import Flask, flash, get_flashed_messages,make_response,redirect, render_template, request, session, url_for
import mysql.connector
import MySQLdb.cursors
import barcode
from barcode.writer import ImageWriter
from PIL import ImageFont
from barcode import UPCA

connection = mysql.connector.connect(host='localhost', database='emar', user='root', password='')
cursor = connection.cursor()
app = Flask(__name__)
app.secret_key = 'your_secret_key' 


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/dashboard')
def home():
    if 'loggedin' in session:
        return render_template('index.html', username=session['username'])
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember')
        cursor.execute('SELECT * FROM user WHERE username=%s and password=%s', (username, password))
        record = cursor.fetchone()
        if record:
            session['loggedin'] = True
            session['username'] = record[1]
            if remember:
                # If the 'remember' checkbox is checked, set a cookie to remember the user
                resp = make_response(redirect(url_for('home')))
                resp.set_cookie('username', username)
                return resp
            return redirect(url_for('home'))
        else:
           flash('Incorrect username or password. Please try again.')
    return render_template('login.html')


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

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        country = request.form['country']
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'User already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s)', (userName, email, password, role, country))
            connection.commit()
            message = 'New user created!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

@app.route('/users')
def users():
    if 'loggedin' in session:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        return render_template('users.html', users=users)
    return redirect(url_for('login'))

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    message = ''
    if 'loggedin' in session:
        editUserId = request.args.get('id')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE id = %s', (editUserId,))
        editUser = cursor.fetchone()
        if request.method == 'POST' and 'name' in request.form and 'id' in request.form and 'role' in request.form and 'country' in request.form:
            userName = request.form['name']
            role = request.form['role']
            country = request.form['country']
            userId = request.form['id']
            if not re.match(r'[A-Za-z0-9]+', userName):
                message = 'Name must contain only characters and numbers!'
            else:
                cursor.execute('UPDATE users SET name=%s, role=%s, country=%s WHERE id=%s', (userName, role, country, userId,))
                connection.commit()
                message = 'User updated!'
                return redirect(url_for('users'))
        elif request.method == 'POST':
            message = 'Please fill out the form!'
        return render_template('edit.html', message=message, editUser=editUser)
    return redirect(url_for('login'))

@app.route('/password_change', methods=['GET', 'POST'])
def password_change():
    message = ''
    if 'loggedin' in session:
        changePassUserId = request.args.get('id')
        if request.method == 'POST' and 'password' in request.form and 'confirm_pass' in request.form and 'userid' in request.form:
            password = request.form['password']
            confirm_pass = request.form['confirm_pass']
            userId = request.form['id']
            if not password or not confirm_pass:
                message = 'Please fill out the form!'
            elif password != confirm_pass:
                message = 'Confirm password is not equal!'
            else:
                cursor = connection.cursor()
                cursor.execute('UPDATE users SET password=%s WHERE id=%s', (password, userId,))
                connection.commit()
                message = 'Password updated!'
        elif request.method == 'POST':
            message = 'Please fill out the form!'
        return render_template('password_change.html', message=message, changePassUserId=changePassUserId)
    return redirect(url_for('login'))

@app.route('/view')
def view():
    if 'loggedin' in session:
        viewUserId = request.args.get('id')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE id = %s', (viewUserId,))
        user = cursor.fetchone()
        return render_template('view.html', user=user)
    return redirect(url_for('login'))

@app.route('/remove/<int:userid>', methods=['GET', 'POST'])
def remove(userid):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM users WHERE id = %s', (userid,))
    connection.commit()
    message ='User deleted!'
    return redirect(url_for('users', message=message))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
