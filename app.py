import random
from flask import Flask, flash, get_flashed_messages, redirect, render_template, request, session, url_for
import mysql.connector
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
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM user WHERE username=%s and password=%s', (username, password))
        record = cursor.fetchone()
        if record:
            session['loggedin'] = True
            session['username'] = record[1]
            return redirect(url_for('home'))
        else:
            msg = 'Invalid username or password'
    return render_template('login.html', msg=msg)


@app.route('/print/<string:barcode_number>', methods=['GET'])
def print(barcode_number):
    return render_template('print-page.html', barcode_number=barcode_number)

@app.route('/insert', methods=['POST'])
def insert():
    if request.method == 'POST':
        p_name = request.form['p_name']
        price = request.form['price']
        quantity = request.form['quantity']

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
        cursor.execute("INSERT INTO product (p_name, price, quantity, barcode) VALUES (%s, %s, %s, %s)", (p_name, price, quantity, barcode_number))
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
        cursor = connection.cursor()
        cursor.execute("UPDATE product SET p_name=%s, price=%s, quantity=%s WHERE id=%s", (p_name, price, quantity, id_data))
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


@app.route('/register')
def register():
    return render_template('register.html')





if __name__ == '__main__':
    app.run(debug=True)