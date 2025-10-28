from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session

# Store last SQL query
last_sql_query = ""

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="010831",
            database="food_ordering_system"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Home Route - Display Menu
@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get sorting parameters
        sort_by = request.args.get('sort_by', 'default')
        order = request.args.get('order', 'ASC')
        group_by = request.args.get('group_by', 'none')
        
        # Get search and filter parameters
        search_term = request.args.get('search', '').strip()
        cuisine_filter = request.args.getlist('cuisine')
        category_filter = request.args.getlist('category')
        
        # Get all data for different tabs
        cursor.execute("SELECT * FROM Customers")
        customers = cursor.fetchall()
        
        # Restaurants with sorting
        restaurant_query = "SELECT * FROM Restaurants"
        if sort_by == 'restaurant_name':
            restaurant_query += f" ORDER BY name {order}"
        elif sort_by == 'rating':
            restaurant_query += f" ORDER BY rating {order}"
        cursor.execute(restaurant_query)
        restaurants = cursor.fetchall()
        session['last_query'] = restaurant_query
        
        # Get all categories for filter checkboxes
        cursor.execute("SELECT DISTINCT name FROM Categories ORDER BY name")
        all_categories = [row['name'] for row in cursor.fetchall()]
        
        # Get all cuisine types for filter checkboxes
        cursor.execute("SELECT DISTINCT cuisine_type FROM Restaurants WHERE cuisine_type IS NOT NULL ORDER BY cuisine_type")
        all_cuisines = [row['cuisine_type'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM Categories")
        categories = cursor.fetchall()
        
        # Menu Items with sorting, search, and filters
        menu_query = """
            SELECT mi.*, r.name AS restaurant_name, r.cuisine_type, c.name AS category_name
            FROM Menu_Items mi
            LEFT JOIN Restaurants r ON mi.restaurant_id = r.restaurant_id
            LEFT JOIN Categories c ON mi.category_id = c.category_id
            WHERE 1=1
        """
        query_params = []
        
        # Add search filter
        if search_term:
            menu_query += " AND (mi.name LIKE %s OR r.name LIKE %s OR mi.description LIKE %s)"
            search_pattern = f"%{search_term}%"
            query_params.extend([search_pattern, search_pattern, search_pattern])
        
        # Add cuisine filter
        if cuisine_filter:
            placeholders = ','.join(['%s'] * len(cuisine_filter))
            menu_query += f" AND r.cuisine_type IN ({placeholders})"
            query_params.extend(cuisine_filter)
        
        # Add category filter
        if category_filter:
            placeholders = ','.join(['%s'] * len(category_filter))
            menu_query += f" AND c.name IN ({placeholders})"
            query_params.extend(category_filter)
        
        # Add sorting
        if sort_by == 'price':
            menu_query += f" ORDER BY mi.price {order}"
        elif sort_by == 'restaurant':
            menu_query += f" ORDER BY r.name {order}"
        elif sort_by == 'category':
            menu_query += f" ORDER BY c.name {order}"
        elif sort_by == 'item_name':
            menu_query += f" ORDER BY mi.name {order}"
        
        cursor.execute(menu_query, query_params)
        menu_items = cursor.fetchall()
        session['last_query'] = menu_query % tuple(query_params) if query_params else menu_query
        
        # Orders with sorting
        order_query = """
            SELECT o.*, c.name AS customer_name, r.name AS restaurant_name
            FROM Orders o
            LEFT JOIN Customers c ON o.customer_id = c.customer_id
            LEFT JOIN Restaurants r ON o.restaurant_id = r.restaurant_id
        """
        if sort_by == 'order_amount':
            order_query += f" ORDER BY o.total_amount {order}"
        elif sort_by == 'order_status':
            order_query += f" ORDER BY o.status {order}"
        elif sort_by == 'order_date':
            order_query += f" ORDER BY o.order_date {order}"
        else:
            order_query += " ORDER BY o.order_date DESC"
        cursor.execute(order_query)
        orders = cursor.fetchall()
        session['last_query'] = order_query
        
        # Deliveries with sorting
        delivery_query = "SELECT * FROM Deliveries"
        if sort_by == 'delivery_status':
            delivery_query += f" ORDER BY delivery_status {order}"
        elif sort_by == 'driver_name':
            delivery_query += f" ORDER BY driver_name {order}"
        cursor.execute(delivery_query)
        deliveries = cursor.fetchall()
        session['last_query'] = delivery_query
        
        # GROUP BY queries
        grouped_data = None
        if group_by == 'restaurant':
            cursor.execute("""
                SELECT r.name AS restaurant_name, COUNT(mi.item_id) AS item_count, 
                       AVG(mi.price) AS avg_price, MIN(mi.price) AS min_price, 
                       MAX(mi.price) AS max_price
                FROM Restaurants r
                LEFT JOIN Menu_Items mi ON r.restaurant_id = mi.restaurant_id
                GROUP BY r.restaurant_id, r.name
                ORDER BY item_count DESC
            """)
            grouped_data = cursor.fetchall()
            session['last_query'] = "SELECT r.name, COUNT(mi.item_id), AVG(mi.price), MIN(mi.price), MAX(mi.price) FROM Restaurants r LEFT JOIN Menu_Items mi ON r.restaurant_id = mi.restaurant_id GROUP BY r.restaurant_id, r.name ORDER BY COUNT(mi.item_id) DESC"
        elif group_by == 'category':
            cursor.execute("""
                SELECT c.name AS category_name, COUNT(mi.item_id) AS item_count,
                       AVG(mi.price) AS avg_price, MIN(mi.price) AS min_price,
                       MAX(mi.price) AS max_price
                FROM Categories c
                LEFT JOIN Menu_Items mi ON c.category_id = mi.category_id
                GROUP BY c.category_id, c.name
                ORDER BY item_count DESC
            """)
            grouped_data = cursor.fetchall()
            session['last_query'] = "SELECT c.name, COUNT(mi.item_id), AVG(mi.price), MIN(mi.price), MAX(mi.price) FROM Categories c LEFT JOIN Menu_Items mi ON c.category_id = mi.category_id GROUP BY c.category_id, c.name ORDER BY COUNT(mi.item_id) DESC"
        elif group_by == 'delivery_status':
            cursor.execute("""
                SELECT o.status AS order_status, COUNT(o.order_id) AS order_count,
                       SUM(o.total_amount) AS total_revenue, AVG(o.total_amount) AS avg_order_value
                FROM Orders o
                GROUP BY o.status
                ORDER BY order_count DESC
            """)
            grouped_data = cursor.fetchall()
            session['last_query'] = "SELECT o.status, COUNT(o.order_id), SUM(o.total_amount), AVG(o.total_amount) FROM Orders o GROUP BY o.status ORDER BY COUNT(o.order_id) DESC"
        elif group_by == 'customer_orders':
            cursor.execute("""
                SELECT c.name AS customer_name, COUNT(o.order_id) AS order_count,
                       SUM(o.total_amount) AS total_spent, AVG(o.total_amount) AS avg_order_value
                FROM Customers c
                LEFT JOIN Orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_id, c.name
                HAVING order_count > 0
                ORDER BY total_spent DESC
            """)
            grouped_data = cursor.fetchall()
            session['last_query'] = "SELECT c.name, COUNT(o.order_id), SUM(o.total_amount), AVG(o.total_amount) FROM Customers c LEFT JOIN Orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.name HAVING COUNT(o.order_id) > 0 ORDER BY SUM(o.total_amount) DESC"
        
        cursor.close()
        conn.close()
        
        return render_template('index.html', 
                             customers=customers,
                             restaurants=restaurants,
                             categories=categories,
                             menu_items=menu_items,
                             orders=orders,
                             deliveries=deliveries,
                             grouped_data=grouped_data,
                             sort_by=sort_by,
                             order=order,
                             group_by=group_by,
                             search_term=search_term,
                             cuisine_filter=cuisine_filter,
                             category_filter=category_filter,
                             all_cuisines=all_cuisines,
                             all_categories=all_categories,
                             last_query=session.get('last_query', ''))
    return "Error connecting to the database."

# ============ CUSTOMERS CRUD ============
@app.route('/add_customer', methods=['POST'])
def add_customer():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = f"INSERT INTO Customers (name, email, phone, password, address) VALUES ('{request.form['name']}', '{request.form['email']}', '{request.form['phone']}', '****', '{request.form['address']}')"
        session['last_query'] = query
        cursor.execute("""
            INSERT INTO Customers (name, email, phone, password, address)
            VALUES (%s, %s, %s, %s, %s)
        """, (request.form['name'], request.form['email'], request.form['phone'],
              request.form['password'], request.form['address']))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_customer/<int:id>', methods=['POST'])
def update_customer(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = f"UPDATE Customers SET name='{request.form['name']}', email='{request.form['email']}', phone='{request.form['phone']}', address='{request.form['address']}' WHERE customer_id={id}"
        session['last_query'] = query
        cursor.execute("""
            UPDATE Customers 
            SET name=%s, email=%s, phone=%s, address=%s
            WHERE customer_id=%s
        """, (request.form['name'], request.form['email'], request.form['phone'],
              request.form['address'], id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"DELETE FROM Customers WHERE customer_id={id}"
        cursor.execute("DELETE FROM Customers WHERE customer_id=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# ============ RESTAURANTS CRUD ============
@app.route('/add_restaurant', methods=['POST'])
def add_restaurant():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"INSERT INTO Restaurants (name, address, phone_number, cuisine_type, rating) VALUES ('{request.form['name']}', '{request.form['address']}', '{request.form['phone_number']}', '{request.form['cuisine_type']}', {request.form['rating']})"
        cursor.execute("""
            INSERT INTO Restaurants (name, address, phone_number, cuisine_type, rating)
            VALUES (%s, %s, %s, %s, %s)
        """, (request.form['name'], request.form['address'], request.form['phone_number'],
              request.form['cuisine_type'], request.form['rating']))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_restaurant/<int:id>', methods=['POST'])
def update_restaurant(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"UPDATE Restaurants SET name='{request.form['name']}', address='{request.form['address']}', phone_number='{request.form['phone_number']}', cuisine_type='{request.form['cuisine_type']}', rating={request.form['rating']} WHERE restaurant_id={id}"
        cursor.execute("""
            UPDATE Restaurants 
            SET name=%s, address=%s, phone_number=%s, cuisine_type=%s, rating=%s
            WHERE restaurant_id=%s
        """, (request.form['name'], request.form['address'], request.form['phone_number'],
              request.form['cuisine_type'], request.form['rating'], id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_restaurant/<int:id>')
def delete_restaurant(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"DELETE FROM Restaurants WHERE restaurant_id={id}"
        cursor.execute("DELETE FROM Restaurants WHERE restaurant_id=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# ============ CATEGORIES CRUD ============
@app.route('/add_category', methods=['POST'])
def add_category():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"INSERT INTO Categories (name) VALUES ('{request.form['name']}')"
        cursor.execute("INSERT INTO Categories (name) VALUES (%s)", (request.form['name'],))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_category/<int:id>', methods=['POST'])
def update_category(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"UPDATE Categories SET name='{request.form['name']}' WHERE category_id={id}"
        cursor.execute("UPDATE Categories SET name=%s WHERE category_id=%s", 
                      (request.form['name'], id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_category/<int:id>')
def delete_category(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"DELETE FROM Categories WHERE category_id={id}"
        cursor.execute("DELETE FROM Categories WHERE category_id=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# ============ MENU ITEMS CRUD ============
@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"INSERT INTO Menu_Items (restaurant_id, name, description, price, image_url, category_id) VALUES ({request.form['restaurant_id']}, '{request.form['name']}', '{request.form['description']}', {request.form['price']}, '{request.form['image_url']}', {request.form['category_id']})"
        cursor.execute("""
            INSERT INTO Menu_Items (restaurant_id, name, description, price, image_url, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (request.form['restaurant_id'], request.form['name'], request.form['description'],
              request.form['price'], request.form['image_url'], request.form['category_id']))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_menu_item/<int:id>', methods=['POST'])
def update_menu_item(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"UPDATE Menu_Items SET restaurant_id={request.form['restaurant_id']}, name='{request.form['name']}', description='{request.form['description']}', price={request.form['price']}, image_url='{request.form['image_url']}', category_id={request.form['category_id']} WHERE item_id={id}"
        cursor.execute("""
            UPDATE Menu_Items 
            SET restaurant_id=%s, name=%s, description=%s, price=%s, image_url=%s, category_id=%s
            WHERE item_id=%s
        """, (request.form['restaurant_id'], request.form['name'], request.form['description'],
              request.form['price'], request.form['image_url'], request.form['category_id'], id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_menu_item/<int:id>')
def delete_menu_item(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"DELETE FROM Menu_Items WHERE item_id={id}"
        cursor.execute("DELETE FROM Menu_Items WHERE item_id=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# ============ ORDERS CRUD ============
@app.route('/add_order', methods=['POST'])
def add_order():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        delivery_id = request.form['delivery_id'] if request.form['delivery_id'] else 'NULL'
        session['last_query'] = f"INSERT INTO Orders (customer_id, restaurant_id, total_amount, status, delivery_id) VALUES ({request.form['customer_id']}, {request.form['restaurant_id']}, {request.form['total_amount']}, '{request.form['status']}', {delivery_id})"
        cursor.execute("""
            INSERT INTO Orders (customer_id, restaurant_id, total_amount, status, delivery_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (request.form['customer_id'], request.form['restaurant_id'], 
              request.form['total_amount'], request.form['status'], 
              request.form['delivery_id'] if request.form['delivery_id'] else None))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_order/<int:id>', methods=['POST'])
def update_order(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        delivery_id = request.form['delivery_id'] if request.form['delivery_id'] else 'NULL'
        session['last_query'] = f"UPDATE Orders SET customer_id={request.form['customer_id']}, restaurant_id={request.form['restaurant_id']}, total_amount={request.form['total_amount']}, status='{request.form['status']}', delivery_id={delivery_id} WHERE order_id={id}"
        cursor.execute("""
            UPDATE Orders 
            SET customer_id=%s, restaurant_id=%s, total_amount=%s, status=%s, delivery_id=%s
            WHERE order_id=%s
        """, (request.form['customer_id'], request.form['restaurant_id'],
              request.form['total_amount'], request.form['status'],
              request.form['delivery_id'] if request.form['delivery_id'] else None, id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_order/<int:id>')
def delete_order(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"DELETE FROM Orders WHERE order_id={id}"
        cursor.execute("DELETE FROM Orders WHERE order_id=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# ============ DELIVERIES CRUD ============
@app.route('/add_delivery', methods=['POST'])
def add_delivery():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"INSERT INTO Deliveries (driver_name, driver_phone, delivery_status) VALUES ('{request.form['driver_name']}', '{request.form['driver_phone']}', '{request.form['delivery_status']}')"
        cursor.execute("""
            INSERT INTO Deliveries (driver_name, driver_phone, delivery_status)
            VALUES (%s, %s, %s)
        """, (request.form['driver_name'], request.form['driver_phone'], 
              request.form['delivery_status']))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_delivery/<int:id>', methods=['POST'])
def update_delivery(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"UPDATE Deliveries SET driver_name='{request.form['driver_name']}', driver_phone='{request.form['driver_phone']}', delivery_status='{request.form['delivery_status']}' WHERE delivery_id={id}"
        cursor.execute("""
            UPDATE Deliveries 
            SET driver_name=%s, driver_phone=%s, delivery_status=%s
            WHERE delivery_id=%s
        """, (request.form['driver_name'], request.form['driver_phone'],
              request.form['delivery_status'], id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_delivery/<int:id>')
def delete_delivery(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        session['last_query'] = f"DELETE FROM Deliveries WHERE delivery_id={id}"
        cursor.execute("DELETE FROM Deliveries WHERE delivery_id=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# ============ INITIALIZE DATABASE WITH DUMMY DATA ============
@app.route('/init_db')
def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Clear existing data (be careful with this in production!)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE Order_Items")
        cursor.execute("TRUNCATE TABLE Orders")
        cursor.execute("TRUNCATE TABLE Menu_Items")
        cursor.execute("TRUNCATE TABLE Deliveries")
        cursor.execute("TRUNCATE TABLE Categories")
        cursor.execute("TRUNCATE TABLE Restaurants")
        cursor.execute("TRUNCATE TABLE Customers")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Insert Customers (20+) - Indian Names
        customers_data = [
            ('Rajesh Kumar', 'rajesh.kumar@email.com', '+91-98765-43210', 'pass123', '12/A, MG Road, Mumbai, Maharashtra'),
            ('Priya Sharma', 'priya.sharma@email.com', '+91-98765-43211', 'pass123', '45, Sector 15, Delhi'),
            ('Amit Patel', 'amit.patel@email.com', '+91-98765-43212', 'pass123', '78, Park Street, Kolkata, West Bengal'),
            ('Sneha Reddy', 'sneha.reddy@email.com', '+91-98765-43213', 'pass123', '23, Banjara Hills, Hyderabad, Telangana'),
            ('Vikram Singh', 'vikram.singh@email.com', '+91-98765-43214', 'pass123', '56, Civil Lines, Jaipur, Rajasthan'),
            ('Kavya Nair', 'kavya.nair@email.com', '+91-98765-43215', 'pass123', '89, MG Road, Kochi, Kerala'),
            ('Rohan Gupta', 'rohan.gupta@email.com', '+91-98765-43216', 'pass123', '34, Whitefield, Bangalore, Karnataka'),
            ('Anjali Verma', 'anjali.verma@email.com', '+91-98765-43217', 'pass123', '67, Cantonment, Pune, Maharashtra'),
            ('Arjun Iyer', 'arjun.iyer@email.com', '+91-98765-43218', 'pass123', '90, Anna Nagar, Chennai, Tamil Nadu'),
            ('Pooja Desai', 'pooja.desai@email.com', '+91-98765-43219', 'pass123', '12, CG Road, Ahmedabad, Gujarat'),
            ('Karan Malhotra', 'karan.malhotra@email.com', '+91-98765-43220', 'pass123', '45, Connaught Place, Delhi'),
            ('Neha Kapoor', 'neha.kapoor@email.com', '+91-98765-43221', 'pass123', '78, Sector 17, Chandigarh'),
            ('Siddharth Joshi', 'siddharth.joshi@email.com', '+91-98765-43222', 'pass123', '23, FC Road, Pune, Maharashtra'),
            ('Riya Agarwal', 'riya.agarwal@email.com', '+91-98765-43223', 'pass123', '56, Park Street, Kolkata'),
            ('Aditya Rao', 'aditya.rao@email.com', '+91-98765-43224', 'pass123', '89, Indiranagar, Bangalore'),
            ('Megha Pillai', 'megha.pillai@email.com', '+91-98765-43225', 'pass123', '34, Marine Drive, Mumbai'),
            ('Rahul Mehta', 'rahul.mehta@email.com', '+91-98765-43226', 'pass123', '67, Saket, Delhi'),
            ('Divya Krishnan', 'divya.krishnan@email.com', '+91-98765-43227', 'pass123', '90, T Nagar, Chennai'),
            ('Varun Chopra', 'varun.chopra@email.com', '+91-98765-43228', 'pass123', '12, Model Town, Ludhiana, Punjab'),
            ('Shreya Bose', 'shreya.bose@email.com', '+91-98765-43229', 'pass123', '45, Salt Lake, Kolkata'),
            ('Nikhil Pandey', 'nikhil.pandey@email.com', '+91-98765-43230', 'pass123', '78, Gomti Nagar, Lucknow, UP'),
            ('Isha Saxena', 'isha.saxena@email.com', '+91-98765-43231', 'pass123', '23, Vijay Nagar, Indore, MP')
        ]
        cursor.executemany("""
            INSERT INTO Customers (name, email, phone, password, address) 
            VALUES (%s, %s, %s, %s, %s)
        """, customers_data)
        
        # Insert Restaurants (20+) - Indian Restaurant Names with login credentials
        restaurants_data = [
            ('Dominos Pizza', 'Shop 12, Phoenix Mall, Mumbai', '+91-022-12345678', 'Italian', 4.5, 'restaurant1', 'password123'),
            ('McDonalds', 'MG Road, Delhi', '+91-011-23456789', 'Fast Food', 4.2, 'restaurant2', 'password123'),
            ('Sushi Bay', 'Cyber Hub, Gurgaon', '+91-124-34567890', 'Japanese', 4.7, 'restaurant3', 'password123'),
            ('Taco Bell', 'Connaught Place, Delhi', '+91-011-45678901', 'Mexican', 4.3, 'restaurant4', 'password123'),
            ('Mainland China', 'Park Street, Kolkata', '+91-033-56789012', 'Chinese', 4.4, 'restaurant5', 'password123'),
            ('Barbeque Nation', 'Indiranagar, Bangalore', '+91-080-67890123', 'Barbecue', 4.6, 'restaurant6', 'password123'),
            ('Pizza Hut', 'Brigade Road, Bangalore', '+91-080-78901234', 'Italian', 4.5, 'restaurant7', 'password123'),
            ('KFC', 'Banjara Hills, Hyderabad', '+91-040-89012345', 'Fast Food', 4.3, 'restaurant8', 'password123'),
            ('Mainland Express', 'Anna Nagar, Chennai', '+91-044-90123456', 'Chinese', 4.4, 'restaurant9', 'password123'),
            ('Burger King', 'Phoenix Mall, Mumbai', '+91-022-01234567', 'Fast Food', 4.2, 'restaurant10', 'password123'),
            ('Barbeque Nation', 'Koramangala, Bangalore', '+91-080-12345678', 'Barbecue', 4.7, 'restaurant11', 'password123'),
            ('Thai Pavilion', 'Vivanta Hotel, Delhi', '+91-011-23456780', 'Thai', 4.5, 'restaurant12', 'password123'),
            ('Mainland China', 'Jubilee Hills, Hyderabad', '+91-040-34567891', 'Chinese', 4.4, 'restaurant13', 'password123'),
            ('Cafe Delhi Heights', 'Rajouri Garden, Delhi', '+91-011-45678902', 'Multi-Cuisine', 4.6, 'restaurant14', 'password123'),
            ('The Korean Restaurant', 'Vasant Kunj, Delhi', '+91-011-56789013', 'Korean', 4.5, 'restaurant15', 'password123'),
            ('Cafe Mondegar', 'Colaba, Mumbai', '+91-022-67890124', 'Continental', 4.3, 'restaurant16', 'password123'),
            ('Pho King Good', 'Hauz Khas, Delhi', '+91-011-78901235', 'Vietnamese', 4.4, 'restaurant17', 'password123'),
            ('Texas Roadhouse', 'Cyber Hub, Gurgaon', '+91-124-89012346', 'American', 4.6, 'restaurant18', 'password123'),
            ('Olive Bar & Kitchen', 'Mehrauli, Delhi', '+91-011-90123457', 'Italian', 4.7, 'restaurant19', 'password123'),
            ('Socials', 'Hauz Khas, Delhi', '+91-011-01234568', 'Multi-Cuisine', 4.4, 'restaurant20', 'password123'),
            ('Hard Rock Cafe', 'Worli, Mumbai', '+91-022-12345679', 'American', 4.5, 'restaurant21', 'password123'),
            ('Subway', 'Sector 18, Noida', '+91-0120-23456780', 'Sandwiches', 4.2, 'restaurant22', 'password123')
        ]
        cursor.executemany("""
            INSERT INTO Restaurants (name, address, phone_number, cuisine_type, rating, username, password) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, restaurants_data)
        
        # Insert Categories (20+)
        categories_data = [
            ('Appetizers',), ('Main Course',), ('Desserts',), ('Beverages',),
            ('Pizza',), ('Burgers',), ('Sushi',), ('Tacos',), ('Noodles',), ('Rice',),
            ('Salads',), ('Soups',), ('Sandwiches',), ('Pasta',), ('Seafood',),
            ('Vegetarian',), ('Vegan',), ('Gluten-Free',), ('Kids Menu',), ('Specials',),
            ('Breakfast',), ('Lunch',), ('Dinner',)
        ]
        cursor.executemany("INSERT INTO Categories (name) VALUES (%s)", categories_data)
        
        # Insert Menu Items (35+) - Mix of Indian and Popular International Dishes
        menu_items_data = [
            (1, 'Margherita Pizza', 'Classic tomato and mozzarella', 299.00, 'https://via.placeholder.com/150', 5),
            (1, 'Farmhouse Pizza', 'Loaded with vegetables', 349.00, 'https://via.placeholder.com/150', 5),
            (2, 'McAloo Tikki Burger', 'Spicy potato patty', 45.00, 'https://via.placeholder.com/150', 6),
            (2, 'McChicken Burger', 'Crispy chicken with lettuce', 149.00, 'https://via.placeholder.com/150', 6),
            (3, 'California Roll', 'Crab, avocado, cucumber', 450.00, 'https://via.placeholder.com/150', 7),
            (3, 'Salmon Nigiri', 'Fresh salmon on rice', 550.00, 'https://via.placeholder.com/150', 7),
            (4, 'Chicken Tacos', 'Three chicken tacos', 199.00, 'https://via.placeholder.com/150', 8),
            (4, 'Veggie Burrito', 'Mexican rice and beans wrap', 189.00, 'https://via.placeholder.com/150', 8),
            (5, 'Chicken Fried Rice', 'Wok-tossed with vegetables', 220.00, 'https://via.placeholder.com/150', 10),
            (5, 'Veg Hakka Noodles', 'Stir-fried noodles', 180.00, 'https://via.placeholder.com/150', 9),
            (6, 'Tandoori Chicken', 'Clay oven roasted chicken', 450.00, 'https://via.placeholder.com/150', 2),
            (6, 'Chicken Tikka Masala', 'Creamy tomato curry', 380.00, 'https://via.placeholder.com/150', 2),
            (7, 'Cheese Garlic Bread', '4 pieces with dip', 99.00, 'https://via.placeholder.com/150', 1),
            (7, 'Pepperoni Pizza', 'Loaded with pepperoni', 399.00, 'https://via.placeholder.com/150', 5),
            (8, 'Zinger Burger', 'Spicy chicken burger', 199.00, 'https://via.placeholder.com/150', 6),
            (8, 'Chicken Popcorn', 'Crispy bite-sized chicken', 149.00, 'https://via.placeholder.com/150', 1),
            (9, 'Schezwan Fried Rice', 'Spicy Indo-Chinese rice', 230.00, 'https://via.placeholder.com/150', 10),
            (9, 'Veg Manchurian', 'Crispy vegetable balls', 200.00, 'https://via.placeholder.com/150', 1),
            (10, 'Whopper Burger', 'Flame-grilled patty', 189.00, 'https://via.placeholder.com/150', 6),
            (10, 'French Fries', 'Crispy golden fries', 79.00, 'https://via.placeholder.com/150', 1),
            (11, 'Paneer Tikka', 'Grilled cottage cheese', 320.00, 'https://via.placeholder.com/150', 1),
            (11, 'Dal Makhani', 'Creamy black lentils', 280.00, 'https://via.placeholder.com/150', 2),
            (12, 'Pad Thai Noodles', 'Thai rice noodles', 350.00, 'https://via.placeholder.com/150', 9),
            (12, 'Thai Green Curry', 'Coconut-based curry', 420.00, 'https://via.placeholder.com/150', 2),
            (13, 'Chicken Chilli', 'Spicy Indo-Chinese chicken', 320.00, 'https://via.placeholder.com/150', 2),
            (14, 'Pasta Alfredo', 'Creamy white sauce pasta', 299.00, 'https://via.placeholder.com/150', 14),
            (15, 'Bibimbap', 'Korean rice bowl', 450.00, 'https://via.placeholder.com/150', 10),
            (16, 'Caesar Salad', 'Fresh greens with dressing', 250.00, 'https://via.placeholder.com/150', 11),
            (17, 'Pho Ga', 'Vietnamese chicken soup', 320.00, 'https://via.placeholder.com/150', 12),
            (18, 'Grilled Chicken Steak', 'With mushroom sauce', 699.00, 'https://via.placeholder.com/150', 2),
            (19, 'Bruschetta', 'Toasted bread with toppings', 280.00, 'https://via.placeholder.com/150', 1),
            (20, 'Butter Chicken', 'Rich tomato cream curry', 420.00, 'https://via.placeholder.com/150', 2),
            (6, 'Chicken Biryani', 'Fragrant rice with spices', 350.00, 'https://via.placeholder.com/150', 10),
            (11, 'Palak Paneer', 'Spinach with cottage cheese', 280.00, 'https://via.placeholder.com/150', 2),
            (13, 'Spring Rolls', 'Crispy vegetable rolls', 180.00, 'https://via.placeholder.com/150', 1),
            (6, 'Masala Dosa', 'Crispy crepe with potato', 120.00, 'https://via.placeholder.com/150', 2)
        ]
        cursor.executemany("""
            INSERT INTO Menu_Items (restaurant_id, name, description, price, image_url, category_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, menu_items_data)
        
        # Insert Deliveries (20+) - Indian Driver Names
        deliveries_data = [
            ('Ravi Kumar', '+91-98765-00001', 'Delivered'),
            ('Suresh Yadav', '+91-98765-00002', 'In Transit'),
            ('Manoj Singh', '+91-98765-00003', 'Pending'),
            ('Deepak Sharma', '+91-98765-00004', 'Delivered'),
            ('Vinod Patel', '+91-98765-00005', 'In Transit'),
            ('Ajay Verma', '+91-98765-00006', 'Delivered'),
            ('Ramesh Kumar', '+91-98765-00007', 'Pending'),
            ('Santosh Reddy', '+91-98765-00008', 'Delivered'),
            ('Prakash Gupta', '+91-98765-00009', 'In Transit'),
            ('Mukesh Jain', '+91-98765-00010', 'Delivered'),
            ('Ashok Desai', '+91-98765-00011', 'Pending'),
            ('Vijay Nair', '+91-98765-00012', 'Delivered'),
            ('Dinesh Iyer', '+91-98765-00013', 'In Transit'),
            ('Anil Kapoor', '+91-98765-00014', 'Delivered'),
            ('Rajendra Rao', '+91-98765-00015', 'Pending'),
            ('Mohan Pillai', '+91-98765-00016', 'Delivered'),
            ('Gopal Menon', '+91-98765-00017', 'In Transit'),
            ('Sanjay Mehta', '+91-98765-00018', 'Delivered'),
            ('Rakesh Chopra', '+91-98765-00019', 'Pending'),
            ('Naresh Bose', '+91-98765-00020', 'Delivered')
        ]
        cursor.executemany("""
            INSERT INTO Deliveries (driver_name, driver_phone, delivery_status) 
            VALUES (%s, %s, %s)
        """, deliveries_data)
        
        # Insert Orders (20+) - Adjusted prices in rupees
        orders_data = [
            (1, 1, 698.00, 'Delivered', 1),
            (2, 2, 194.00, 'In Transit', 2),
            (3, 3, 1200.00, 'Pending', 3),
            (4, 4, 388.00, 'Delivered', 4),
            (5, 5, 400.00, 'In Transit', 5),
            (6, 6, 1000.00, 'Delivered', 6),
            (7, 7, 448.00, 'Pending', 7),
            (8, 8, 348.00, 'Delivered', 8),
            (9, 9, 430.00, 'In Transit', 9),
            (10, 10, 268.00, 'Delivered', 10),
            (11, 11, 700.00, 'Pending', 11),
            (12, 12, 770.00, 'Delivered', 12),
            (13, 13, 380.00, 'In Transit', 13),
            (14, 14, 299.00, 'Delivered', 14),
            (15, 15, 450.00, 'Pending', 15),
            (16, 16, 250.00, 'Delivered', 16),
            (17, 17, 320.00, 'In Transit', 17),
            (18, 18, 699.00, 'Delivered', 18),
            (19, 19, 280.00, 'Pending', 19),
            (20, 20, 299.00, 'Delivered', 20),
            (1, 5, 620.00, 'Delivered', 1),
            (3, 11, 1050.00, 'In Transit', 2)
        ]
        cursor.executemany("""
            INSERT INTO Orders (customer_id, restaurant_id, total_amount, status, delivery_id) 
            VALUES (%s, %s, %s, %s, %s)
        """, orders_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        return "Database initialized with dummy data!"
    return "Error connecting to the database."

if __name__ == '__main__':
    app.run(debug=True)