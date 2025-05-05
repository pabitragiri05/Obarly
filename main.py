# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Use environment variable for secret key

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# MongoDB setup
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
database_name = os.getenv('DATABASE_NAME', 'Inventory')
client = MongoClient(mongodb_uri)
db = client[database_name]
products_collection = db["Products"]
users_collection = db["Users"]  # New collection for users

# Session setup for cart & wishlist
def init_cart_wishlist():
    session.setdefault('cart', [])
    session.setdefault('wishlist', [])
    # Ensure cart items have quantity
    for item in session['cart']:
        if isinstance(item, str):  # If old format (just product ID)
            session['cart'].remove(item)
            session['cart'].append({'product_id': item, 'quantity': 1})
    session.modified = True

# --- Home and Product Pages ---

@app.route('/')
def index():
    init_cart_wishlist()

    # Get unique categories from the database
    categories = products_collection.distinct("categories")

    # Prepare a list of categories with up to 5 products each
    categorized_products = []
    for category in categories:
        products = list(products_collection.find({"categories": category}).limit(5))
        if products:
            categorized_products.append({
                "category_name": category,
                "products": products
            })

    # Create a map of product IDs to quantities
    cart_quantities = {item['product_id']: item['quantity'] for item in session.get('cart', [])}

    # Fetch recent orders if user is logged in
    recent_orders = []
    if session.get('user_id'):
        recent_orders = list(db['Orders'].find({
            'customer.email': session.get('user_email')
        }).sort('created_at', -1).limit(3))

    return render_template('index.html', 
                         categorized_products=categorized_products, 
                         wishlist=session.get('wishlist', []),
                         cart_quantities=cart_quantities,
                         user_name=session.get('user_name'),
                         recent_orders=recent_orders)

@app.route('/about')
def about():
    init_cart_wishlist()
    return render_template('about_us.html')

@app.route('/checkout')
def checkout():
    init_cart_wishlist()
    
    # Fetch products in cart and calculate total
    products = get_cart_products()
    if not products:  # If cart is empty
        flash('Your cart is empty. Please add items to proceed to checkout.', 'error')
        return redirect(url_for('cart'))
        
    total_price = sum([product['price'] * product['quantity'] for product in products])
    if total_price == 0:  # If total is 0
        flash('Your cart total is 0. Please add items to proceed to checkout.', 'error')
        return redirect(url_for('cart'))
        
    tax = total_price * 0.18
    
    return render_template('checkout.html', products=products, total_price=total_price, tax=tax)

@app.route('/admin')
def admin():
    if session.get('user_role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    products = list(products_collection.find())
    users = list(users_collection.find({}, {'password': 0}))  # Exclude password field
    orders = list(db['Orders'].find().sort('created_at', -1))  # Get all orders sorted by date
    
    return render_template('admin.html', products=products, users=users, orders=orders)

@app.route('/search')
def search():
    init_cart_wishlist()
    
    # Get search query from URL parameters
    query = request.args.get('q', '').strip().lower()
    
    # If query is empty, redirect to products page
    if not query:
        return redirect(url_for('product'))
    
    # Search in product name and description
    products = list(products_collection.find({
        "$or": [
            {"product_name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    }))
    
    # Format products for display
    formatted_products = []
    for p in products:
        formatted_products.append({
            '_id': str(p['_id']),
            'name': p.get('product_name', 'No name'),
            'description': p.get('description', ''),
            'price': p.get('default_price', 0),
            'image': p.get('image_path', '').split('#')[0] if p.get('image_path') else '',
            'category': p.get('categories', ''),
            'subcategory': p.get('Sub_category', '')
        })
    
    # Create a map of product IDs to quantities
    cart_quantities = {item['product_id']: item['quantity'] for item in session.get('cart', [])}
    
    return render_template('search.html', 
                         products=formatted_products, 
                         query=query,
                         wishlist=session.get('wishlist', []),
                         cart_quantities=cart_quantities)

@app.route('/product')
def product():
    init_cart_wishlist()
    
    # Get search query from URL parameters
    query = request.args.get('q', '').strip().lower()
    
    # Get selected category and subcategory from URL query params
    selected_category = request.args.get('category', '').strip().lower()
    selected_subcategory = request.args.get('subcategory', '').strip().lower()

    # Fetch categories and subcategories from the database
    categories = list(set([cat.get('categories', '') for cat in products_collection.find({}, {"categories": 1})]))
    categories = sorted(categories)  # Sort categories alphabetically
    
    raw_subcategories = products_collection.find({"categories": {"$regex": f"^{selected_category}$", "$options": "i"}}, {"Sub_category": 1})

    # Process and get subcategories
    subcategories_set = set()
    for item in raw_subcategories:
        subcat_field = item.get("Sub_category", "")
        if subcat_field:
            subcategories = [s.strip() for s in subcat_field.split(",") if s.strip()]
            subcategories_set.update(subcategories)
    subcategories = sorted(subcategories_set)  # Sort subcategories alphabetically

    # Build product query
    product_query = {}
    if selected_category:
        product_query["categories"] = {"$regex": f"^{selected_category}$", "$options": "i"}
    if selected_subcategory:
        product_query["Sub_category"] = {"$regex": f"^{selected_subcategory}$", "$options": "i"}
    if query:
        product_query["$or"] = [
            {"product_name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]

    # Fetch filtered products
    products = []
    for p in products_collection.find(product_query):
        products.append({
            '_id': str(p.get('_id')),
            'name': p.get('product_name', 'No name'),
            'description': p.get('description', ''),
            'price': p.get('default_price', 0),
            'image': p.get('image_path', '').split('#')[0] if p.get('image_path') else ''
        })

    # Create a map of product IDs to quantities
    cart_quantities = {item['product_id']: item['quantity'] for item in session.get('cart', [])}

    return render_template(
        'product.html',
        products=products,
        categories=categories,
        subcategories=subcategories,
        selected_category=selected_category,
        selected_subcategory=selected_subcategory,
        query=query,
        wishlist=session.get('wishlist', []),
        cart_quantities=cart_quantities
    )

@app.route('/product-view/<product_id>')
def product_view(product_id):
    # Fetch selected product details by ID
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if product:
        category = product.get('categories', '')
        subcategories = product.get('Sub_category', '')
        subcat_list = [s.strip() for s in subcategories.split(",") if s.strip()]
        
        # Fetch similar products based on the category and subcategory
        similar_products = list(products_collection.find({
            "categories": category,
            "Sub_category": {"$in": subcat_list},
            "_id": {"$ne": product["_id"]}
        }).limit(4))

        # Create a map of product IDs to quantities
        cart_quantities = {item['product_id']: item['quantity'] for item in session.get('cart', [])}
        
        return render_template('product-view.html', 
                             product=product, 
                             similar_products=similar_products,
                             cart_quantities=cart_quantities)
    return "Product not found", 404

# --- Cart and Wishlist ---

@app.route('/add-to-cart/<product_id>')
def add_to_cart(product_id):
    init_cart_wishlist()
    
    # Get quantity from query parameter, default to 1
    quantity = int(request.args.get('quantity', 1))
    
    # If quantity is 0, remove the product from cart
    if quantity == 0:
        session['cart'] = [item for item in session.get('cart', []) if item['product_id'] != product_id]
        session.modified = True
        return jsonify({"status": "success", "quantity": 0})
    
    # Check if product already in cart
    for item in session['cart']:
        if item['product_id'] == product_id:
            # Update existing quantity
            item['quantity'] = quantity
            session.modified = True
            return jsonify({"status": "success", "quantity": quantity})
    
    # Add new product to cart with quantity
    session['cart'].append({'product_id': product_id, 'quantity': quantity})
    session.modified = True
    
    return jsonify({"status": "success", "quantity": quantity})

def get_cart_products():
    # Get products based on cart items in session
    product_ids = [ObjectId(item['product_id']) for item in session.get('cart', [])]
    products = list(products_collection.find({"_id": {"$in": product_ids}}))
    
    # Create a map of product IDs to quantities
    quantity_map = {item['product_id']: item['quantity'] for item in session.get('cart', [])}
    
    for product in products:
        product['price'] = product.get('default_price', 0)
        product['name'] = product.get('product_name', 'No name')
        product['image'] = product.get('image_path', '').split('#')[0] if product.get('image_path') else ''
        product['_id'] = str(product['_id'])
        product['quantity'] = quantity_map.get(str(product['_id']), 1)
    return products

@app.route('/cart')
def cart():
    init_cart_wishlist()
    
    # Fetch products in cart and calculate total
    products = get_cart_products()
    total_price = sum([product['price'] * product['quantity'] for product in products])
    tax = total_price * 0.18
    
    return render_template('cart.html', products=products, total_price=total_price, tax=tax)

@app.route('/update-cart-quantity/<product_id>', methods=['POST'])
def update_cart_quantity(product_id):
    init_cart_wishlist()
    
    quantity = int(request.form.get('quantity', 1))
    
    # Update quantity in cart
    for item in session['cart']:
        if item['product_id'] == product_id:
            item['quantity'] = quantity
            session.modified = True
            return jsonify({"status": "success", "quantity": quantity})
    
    return jsonify({"status": "error", "message": "Product not found in cart"})

@app.route('/remove-from-cart/<product_id>')
def remove_from_cart(product_id):
    # Remove product from cart
    session['cart'] = [item for item in session.get('cart', []) if item['product_id'] != product_id]
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/clear-cart')
def clear_cart():
    # Clear all items from cart
    session['cart'] = []
    session.modified = True
    return redirect(url_for('cart'))

# --- Wishlist Features ---

@app.route('/add_to_wishlist/<product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    init_cart_wishlist()
    
    if product_id not in session['wishlist']:
        session['wishlist'].append(product_id)
        session.modified = True
        return jsonify({"status": "success", "message": "Added to wishlist"})
    else:
        return jsonify({"status": "error", "message": "Already in wishlist"})

@app.route('/remove_from_wishlist/<product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    init_cart_wishlist()
    
    if product_id in session['wishlist']:
        session['wishlist'].remove(product_id)
        session.modified = True
        return jsonify({"status": "success", "message": "Removed from wishlist"})
    else:
        return jsonify({"status": "error", "message": "Not in wishlist"})

@app.route('/wishlist')
def wishlist():
    init_cart_wishlist()
    
    # Fetch products in wishlist
    product_ids = [ObjectId(pid) for pid in session.get('wishlist', [])]
    products = list(products_collection.find({"_id": {"$in": product_ids}}))
    
    # Format products for display
    formatted_products = []
    for p in products:
        formatted_products.append({
            '_id': str(p['_id']),
            'name': p.get('product_name', 'No name'),
            'description': p.get('description', ''),
            'price': p.get('default_price', 0),
            'image': p.get('image_path', '').split('#')[0] if p.get('image_path') else ''
        })
    
    # Create a map of product IDs to quantities
    cart_quantities = {item['product_id']: item['quantity'] for item in session.get('cart', [])}
    
    return render_template('wishlist.html', 
                         products=formatted_products,
                         cart_quantities=cart_quantities)

# --- Admin Product Management ---

@app.route('/admin-login', methods=['POST'])
def admin_login():
    admin_email = request.form['adminEmail']
    admin_password = request.form['adminPassword']
    
    # Simple authentication for admin
    if admin_email == "admin@example.com" and admin_password == "adminpassword123":
        session['admin_logged_in'] = True
        return redirect(url_for('admin'))  # Changed from admin_dashboard to admin
    else:
        return redirect(url_for('index'))  # Redirect to home page if login fails

@app.route('/admin-dashboard')
def admin_dashboard():
    # Only allow admin to access this page
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
    
    # Fetch and show all products
    products = list(products_collection.find())
    return render_template('admin.html', products=products)

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    # Handle form submission to add a new product
    product_name = request.form.get('product_name')
    price = float(request.form.get('price'))
    categories = request.form.get('categories').split(',')
    description = request.form.get('description')
    image = request.form.get('image')
    
    # Insert product data into the database
    product_data = {
        'product_name': product_name,
        'default_price': price,
        'categories': [category.strip() for category in categories],
        'description': description,
        'image_path': image
    }
    products_collection.insert_one(product_data)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit-product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    # Fetch product details and allow editing
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        price = float(request.form.get('price'))
        categories = request.form.get('categories').split(',')
        description = request.form.get('description')
        image = request.form.get('image')
        
        updated_data = {
            'product_name': product_name,
            'default_price': price,
            'categories': [category.strip() for category in categories],
            'description': description,
            'image_path': image
        }
        
        # Update product details in the database
        products_collection.update_one({"_id": ObjectId(product_id)}, {"$set": updated_data})
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit-product.html', product=product)

@app.route('/admin/delete-product/<product_id>')
def delete_product(product_id):
    # Delete product from database
    products_collection.delete_one({"_id": ObjectId(product_id)})
    return redirect(url_for('admin_dashboard'))

@app.route('/search-suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        return jsonify([])
    
    # Search for matching products
    products = list(products_collection.find({
        "$or": [
            {"product_name": {"$regex": f"^{query}", "$options": "i"}},
            {"description": {"$regex": f"^{query}", "$options": "i"}}
        ]
    }).limit(5))
    
    # Format suggestions
    suggestions = []
    for product in products:
        suggestions.append({
            'id': str(product['_id']),
            'name': product.get('product_name', ''),
            'description': product.get('description', ''),
            'image': product.get('image_path', '').split('#')[0] if product.get('image_path') else ''
        })
    
    return jsonify(suggestions)

# --- User Authentication Routes ---

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = users_collection.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        session['user_email'] = email
        session['user_role'] = user['role']
        flash('Login successful!', 'success')
        
        # Redirect admin users to admin panel
        if user['role'] == 'admin':
            return redirect(url_for('admin'))
        
        return redirect(url_for('index'))
    else:
        flash('Invalid email or password', 'error')
        return redirect(url_for('index'))

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Check if user already exists
    if users_collection.find_one({'email': email}):
        flash('Email already registered', 'error')
        return redirect(url_for('index'))
    
    # Hash the password
    hashed_password = generate_password_hash(password)
    
    # Set role based on email
    role = 'admin' if email == 'nkgiri1977@gmail.com' else 'user'
    
    # Create new user
    user = {
        'name': name,
        'email': email,
        'password': hashed_password,
        'role': role,
        'created_at': datetime.now()
    }
    
    users_collection.insert_one(user)
    
    # Set session variables
    session['user_id'] = str(user['_id'])
    session['user_name'] = name
    session['user_email'] = email
    session['user_role'] = role
    
    flash('Registration successful!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin/users')
def admin_users():
    if session.get('user_role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    users = list(users_collection.find({}, {'password': 0}))
    return render_template('admin_users.html', users=users)

@app.route('/admin/toggle-user-role/<user_id>')
def toggle_user_role(user_id):
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        new_role = 'admin' if user['role'] == 'user' else 'user'
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'role': new_role}}
        )
        return jsonify({'success': True, 'new_role': new_role})
    return jsonify({'error': 'User not found'}), 404

# --- Order Placement ---

@app.route('/place-order', methods=['POST'])
def place_order():
    if not session.get('cart'):
        return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400

    # Check if user is logged in
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login to place an order'}), 401

    try:
        data = request.get_json()
        customer = data.get('customer')
        address = data.get('address')
        payment_method = data.get('payment_method')
        products = get_cart_products()
        
        if not products:
            return jsonify({'status': 'error', 'message': 'No products in cart'}), 400
            
        total_price = sum([product['price'] * product['quantity'] for product in products])
        tax = total_price * 0.18
        grand_total = total_price + tax

        # Save order to Orders collection
        order = {
            'customer': {
                'email': session.get('user_email'),
                'first_name': customer.get('first_name', ''),
                'last_name': customer.get('last_name', ''),
                'phone': customer.get('phone', '')
            },
            'address': address,
            'payment_method': payment_method,
            'products': products,
            'total_price': total_price,
            'tax': tax,
            'grand_total': grand_total,
            'status': 'Placed',
            'created_at': datetime.utcnow()
        }
        
        # Insert order and get the result
        result = db['Orders'].insert_one(order)
        
        # Clear cart
        session['cart'] = []
        session.modified = True

        return jsonify({
            'status': 'success', 
            'message': 'Order placed successfully!',
            'order_id': str(result.inserted_id)
        })
    except Exception as e:
        print(f"Error placing order: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to place order. Please try again.'}), 500

@app.route('/my-orders')
def my_orders():
    if not session.get('user_id'):
        flash('Please login to view your orders', 'error')
        return redirect(url_for('index'))
    
    # Get user email from session
    user_email = session.get('user_email')
    if not user_email:
        flash('User email not found', 'error')
        return redirect(url_for('index'))
    
    try:
        # Fetch all orders for the current user, sorted by date (newest first)
        orders = list(db['Orders'].find({
            'customer.email': user_email
        }).sort('created_at', -1))
        
        # Convert ObjectId to string and format dates
        for order in orders:
            order['_id'] = str(order['_id'])
            # Ensure created_at is a datetime object
            if isinstance(order.get('created_at'), str):
                order['created_at'] = datetime.fromisoformat(order['created_at'])
            elif not isinstance(order.get('created_at'), datetime):
                order['created_at'] = datetime.utcnow()
        
        # Debug information
        print(f"Found {len(orders)} orders for user {user_email}")
        
        return render_template('my_orders.html', orders=orders)
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        flash('Error fetching orders. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/cancel-order/<order_id>', methods=['POST'])
def cancel_order(order_id):
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login to cancel orders'}), 401

    try:
        # Get the order
        order = db['Orders'].find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404

        # Check if the order belongs to the current user
        if order['customer']['email'] != session.get('user_email'):
            return jsonify({'status': 'error', 'message': 'Unauthorized to cancel this order'}), 403

        # Check if order can be cancelled (only 'Placed' orders can be cancelled)
        if order['status'] != 'Placed':
            return jsonify({'status': 'error', 'message': 'This order cannot be cancelled'}), 400

        # Update order status to cancelled
        db['Orders'].update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': 'Cancelled'}}
        )

        return jsonify({'status': 'success', 'message': 'Order cancelled successfully'})
    except Exception as e:
        print(f"Error cancelling order: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to cancel order'}), 500

@app.route('/admin/orders')
@login_required
def admin_orders():
    if session.get('user_role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get all orders sorted by date
    orders = list(db.Orders.find().sort('created_at', -1))
    # Get all users for the filter
    users = list(users_collection.find({}, {'password': 0}))
    
    return render_template('admin_orders.html', orders=orders, users=users)

@app.route('/admin/update-order-status/<order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied. Admin privileges required.'})
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'error': 'Status is required'})
        
        # Update order status
        db.Orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': new_status}}
        )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/customer-orders/<customer_email>')
@login_required
def admin_customer_orders(customer_email):
    if session.get('user_role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get all orders for the specific customer, sorted by date
    orders = list(db.Orders.find({'customer.email': customer_email}).sort('created_at', -1))
    
    # Get customer details
    customer = users_collection.find_one({'email': customer_email}, {'password': 0})
    
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_customer_orders.html', 
                         orders=orders, 
                         customer=customer)

# --- Run Flask App ---
if __name__ == '__main__':
    app.run(debug=True)