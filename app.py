from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

# ---------------- ADMIN PROTECTION ----------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(full_name,email,password) VALUES(%s,%s,%s)",
                    (name,email,password))
        mysql.connection.commit()
        cur.close()
        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['is_admin'] = user[4]
            return redirect('/products')

    return render_template('login.html')


# ---------------- PRODUCTS ----------------
@app.route('/products')
def products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template('products.html', products=products)


# ---------------- ADD TO CART ----------------
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO cart(user_id,product_id) VALUES(%s,%s)",
                (session['user_id'],id))
    mysql.connection.commit()
    cur.close()
    return redirect('/cart')


# ---------------- CART ----------------
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT products.id, products.name, products.price 
        FROM cart 
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=%s
    """, [session['user_id']])
    items = cur.fetchall()
    cur.close()
    return render_template('cart.html', items=items)


# ---------------- CHECKOUT ----------------
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO orders(user_id) VALUES(%s)", [session['user_id']])
    cur.execute("DELETE FROM cart WHERE user_id=%s", [session['user_id']])
    mysql.connection.commit()
    cur.close()

    return redirect('/success')


# ---------------- SUCCESS ----------------
@app.route('/success')
def success():
    return render_template('success.html')


# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html')


# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
@admin_required
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template('admin.html', products=products)


@app.route('/admin/add', methods=['POST'])
@admin_required
def add_product():
    name = request.form['name']
    price = request.form['price']
    image = request.form['image']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO products(name,price,image) VALUES(%s,%s,%s)",
                (name,price,image))
    mysql.connection.commit()
    cur.close()
    return redirect('/admin')


@app.route('/admin/edit/<int:id>', methods=['GET','POST'])
@admin_required
def edit_product(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        image = request.form['image']

        cur.execute("""
            UPDATE products SET name=%s,price=%s,image=%s WHERE id=%s
        """,(name,price,image,id))
        mysql.connection.commit()
        cur.close()
        return redirect('/admin')

    cur.execute("SELECT * FROM products WHERE id=%s",[id])
    product = cur.fetchone()
    cur.close()
    return render_template('edit_product.html', product=product)


@app.route('/admin/delete/<int:id>')
@admin_required
def delete_product(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id=%s",[id])
    mysql.connection.commit()
    cur.close()
    return redirect('/admin')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True , port=5000 , host="0.0.0.0")

