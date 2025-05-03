from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_session import Session
import MySQLdb.cursors


app = Flask(__name__)
CORS(app, supports_credentials=True)

# Secret key for session management (ensure to keep it secure in production)
app.secret_key = 'FlaskSecretKey' 
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Mysql@121'
app.config['MYSQL_DB'] = 'artisano'

mysql = MySQL(app)

# Home Route
@app.route('/')
def home():
    logged_in = 'user_id' in session
    username = session.get('firstname') if logged_in else None
    return render_template('index.html', logged_in=logged_in, username=username)

# SHOP PAGE
@app.route('/shop.html')
def shop():
    return render_template('shop.html')

@app.context_processor
def inject_user():
    return dict(logged_in=('user_id' in session))

@app.before_request
def require_login():
    if not session.get('user_id') and request.path.startswith('/profile'):
        return redirect(url_for('login'))
    
# ABOUT PAGE
@app.route('/about.html')
def about():
    return render_template('about.html')

# NEW ARRIVALS PAGE
@app.route('/new-arrivals')
def new_arrivals():
    return "<h1>New Arrivals page coming soon</h1>"

# BRANDS PAGE
@app.route('/brands')
def brands():
    return render_template('brands.html')

@app.route('/categories')
def categories():
    return "<h1>Categories page coming soon</h1>"

#CONTACT PAGE
@app.route('/contact')
def contact():
    return "<h1>Contact page coming soon</h1>"

# PROFILE PAGE
@app.route('/profile.html')
def profile():
    if 'user_id' in session:
        return render_template('profile.html')
    else:
        return redirect(url_for('login_page'))  

# FETCH PERSONAL DETAILS
@app.route('/profile/personal')
def profile_personal():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT firstname, lastname, email FROM users WHERE id = %s", [user_id])
    user_data = cur.fetchone()

    if user_data:
        return jsonify({
            "firstname": user_data[0],
            "lastname": user_data[1],
            "email": user_data[2]
        })
    else:
        return jsonify({"error": "User not found"}), 404

# FETCH ORDERS
@app.route('/profile/orders')
def profile_orders():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT product_id, quantity FROM cart WHERE user_id = %s", [user_id])
    cart_items = cur.fetchall()
    
    orders_list = []
    for item in cart_items:
        cur.execute("SELECT title FROM products WHERE id = %s", [item[0]])
        product = cur.fetchone()
        if product:
            orders_list.append({
                "product_name": product[0],
                "quantity": item[1]
            })
    
    return jsonify({"orders": orders_list})


# SIGNUP ROUTE 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if the user is logged in
    logged_in = 'user_id' in session

    if request.method == 'GET':
        return render_template('signup.html', logged_in=logged_in) 

    data = request.json
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    email = data.get('email')
    password = data.get('password')

    if not (firstname and lastname and email and password):
        return jsonify({'error': 'All fields are required'}), 400

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("INSERT INTO users (firstname, lastname, email, password) VALUES (%s, %s, %s, %s)",
                       (firstname, lastname, email, password))
        mysql.connection.commit()
        return jsonify({'message': 'Your Artisano journey begins now! Happy browsing.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

# LOGIN ROUTE 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Handle login POST logic
    data = request.get_json()
    email = data.get('email').strip()
    password = data.get('password').strip()

    if not (email and password):
        return jsonify({'error': 'Email and password are required'}), 400

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT id, firstname, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({'error': 'Invalid email or password'}), 401

        user_id, firstname, stored_password = user

        if stored_password == password:
            session['user_id'] = user_id
            session['firstname'] = firstname
            return jsonify({'message': 'Login successful', 'user': firstname}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

# LOGOUT ROUTE
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('home')) 

# CHECK LOGIN STATUS
@app.route('/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        return jsonify({'loggedIn': True, 'user': session['firstname']}), 200
    return jsonify({'loggedIn': False}), 200

# PRODUCT MANAGEMENT
@app.route('/api/products')
def get_products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, price, old_price, rating, image, description FROM products")
    products = cur.fetchall()
    cur.close()

    product_list = [{
        "id": row[0],
        "title": row[1],
        "price": row[2],
        "old_price": row[3],
        "rating": row[4],
        "image": row[5],
        "description": row[6]
    } for row in products]

    return jsonify({"products": product_list})

@app.route('/product/<id>')
def product_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, price, old_price, rating, image, description FROM products WHERE id = %s", [id])
    product = cur.fetchone()
    cur.close()

    if not product:
        return "Product not found", 404
    
    product_data = {
        "id": product[0],
        "title": product[1],
        "price": product[2],
        "old_price": product[3],
        "rating": product[4],
        "image": product[5],
        "description": product[6]
    }
    
    return render_template('product.html', product=product_data)

# CART PAGE
@app.route('/cart.html')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = %s", (user_id,))
    items = cursor.fetchall()

    cart_items = []
    subtotal = 0
    discount_percentage = 10  # 
    for row in items:
        product_id, quantity = row
        cursor.execute("SELECT title, price, image FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if product:
            title, price, image = product
            item_total = price * quantity
            subtotal += item_total
            cart_items.append({
                "id": product_id,
                "title": title,
                "price": price,
                "quantity": quantity,
                "image": image,
                "size": "M",  # placeholder
                "color": "Brown"  # placeholder
            })

    discount = subtotal * discount_percentage / 100
    total = subtotal - discount

    return render_template('cart.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           discount_percentage=discount_percentage,
                           discount=discount,
                           total=total)


# ADD TO CART
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    user_id = session['user_id']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE user_id = %s AND product_id = %s",
                       (quantity, user_id, product_id))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                       (user_id, product_id, quantity))
    
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Item added to cart'}), 200

# FETCH CART ITEMS
@app.route('/api/cart')
def get_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = %s", (user_id,))
    items = cursor.fetchall()

    cart_items = []
    subtotal = 0
    discount_percentage = 10

    for row in items:
        product_id, quantity = row
        cursor.execute("SELECT title, price, image FROM products WHERE id = %s", [product_id])
        product = cursor.fetchone()
        if product:
            title, price, image = product
            item_total = price * quantity
            subtotal += item_total
            cart_items.append({
                "id": product_id,
                "title": title,
                "quantity": quantity,
                "price": price,
                "image": image,
            })

    cursor.close()

    discount = subtotal * discount_percentage / 100
    total = subtotal - discount 

    return jsonify({
        "items": cart_items,
        "subtotal": subtotal,
        "discount_percentage": discount_percentage,
        "discount": discount,
        "total": total
    })

# REMOVE FROM CART
@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True}), 200

#UPDATE CART ITEM
@app.route('/api/cart/update/<int:product_id>', methods=['POST'])
def update_cart_item(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.get_json()
    change = data.get('change', 0)
    user_id = session['user_id']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    item = cursor.fetchone()

    if item:
        new_quantity = item[0] + change
        if new_quantity <= 0:
            cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        else:
            cursor.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
                           (new_quantity, user_id, product_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'new_quantity': max(new_quantity, 0)})
    else:
        cursor.close()
        return jsonify({'error': 'Item not found'}), 404
    
# CHECKOUT PAGE
@app.route('/checkout')
def checkout():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT firstname, lastname, email FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()

    cur.execute("""
        SELECT c.product_id, p.title, p.price, c.quantity 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = %s
    """, (user_id,))
    cart_data = cur.fetchall()

    cart_items = []
    subtotal = 0
    for item in cart_data:
        item_total = item['price'] * item['quantity']
        subtotal += item_total
        cart_items.append({
            'title': item['title'],
            'price': item['price'],
            'quantity': item['quantity']
        })

    total = subtotal

    return render_template('checkout.html',
                           user=user_data,
                           cart_items=cart_items,
                           subtotal=subtotal,
                           total=total)


@app.route('/place-order', methods=['POST'])
def place_order():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    zip_code = request.form['zip']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT c.product_id, p.price, c.quantity 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cur.fetchall()

    if not cart_items:
        return "Cart is empty", 400

    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    cur.execute("""
        INSERT INTO orders (
            user_id, total_amount, billing_firstname, billing_lastname, 
            billing_email, billing_phone, billing_address, city, state, zip_code
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, total_amount, firstname, lastname, email, phone,
        address, city, state, zip_code
    ))
    mysql.connection.commit()
    order_id = cur.lastrowid

    for item in cart_items:
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (
            order_id, item['product_id'], item['quantity'], item['price']
        ))
    mysql.connection.commit()

    cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    mysql.connection.commit()

    shipping_info = {
        'firstname': firstname,
        'lastname': lastname,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'state': state,
        'zip': zip_code
    }

    return render_template('successful.html', order_id=order_id, shipping_info=shipping_info)

if __name__ == '__main__':
    app.run(debug=True)
