import random
from flask import Flask, flash, get_flashed_messages, make_response, redirect, render_template, request, session, url_for
import mysql.connector
import barcode
from barcode.writer import SVGWriter
from PIL import ImageFont

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
        # Check if all required fields are present in the request
        if not all([p_name, price, quantity, m_category]):
            flash("All fields are required")
            return redirect(url_for('product'))
        # Generate the barcode number
        barcode_number = generate_random_number()
        # Add product info to the barcode
        product_info = f"{barcode_number}\n PHP {price}.00 - {p_name}"
        # Set the barcode format
        barcode_format = barcode.get_barcode_class('code39')
        # Configure barcode saving options
        saving_options = {
            'quiet_zone': 2.0,
            'font_size': 8,
            'text_distance': 3.0
        }
        # Generate the barcode image and save it as an SVG file
        barcode_path = f"static/img/{barcode_number}"
        barcode_image = barcode_format(barcode_number, writer=SVGWriter(), add_checksum=False)
        barcode_image.save(barcode_path, options=saving_options, text=product_info)

        cursor = connection.cursor()
        cursor.execute("INSERT INTO product (p_name, price, quantity, m_category, barcode) VALUES (%s, %s, %s, %s, %s)", (p_name, price, quantity, m_category, barcode_number))
        connection.commit()

        flash("Data Inserted Successfully")
        return redirect(url_for('product'))


def generate_random_number():
    number = ""
    for i in range(6):
        number += str(random.randint(0, 9))
    return number


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


@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)