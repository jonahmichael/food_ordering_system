# Food Ordering System - Advanced DBMS Project

Welcome to the Food Ordering System, a comprehensive web application built with **Flask** and **MySQL**. This project is designed as an educational tool to demonstrate a wide range of advanced Database Management System (DBMS) operations in a real-world context.

The standout feature is a **live SQL query display**, which shows the exact SQL command executed for every action you perform—from searching and filtering to creating and updating records. This provides immediate insight into how front-end interactions translate into database queries.


<img width="1898" height="873" alt="image" src="https://github.com/user-attachments/assets/1ed05178-f6a8-409e-b81f-73da0ebdc352" />
<img width="1832" height="814" alt="image" src="https://github.com/user-attachments/assets/69eb89ef-a294-4325-a78d-2c3246c0cbe3" />

---

## Key Features

-   **Full CRUD Functionality**: Create, Read, Update, and Delete operations for all database tables (Restaurants, Menu Items, Customers, Orders, etc.).
-   **Advanced Search & Filtering**:
    -   Full-text search across multiple fields using the SQL `LIKE` operator.
    -   Filter data by multiple criteria (e.g., cuisine, category) using the SQL `IN` clause.
-   **Dynamic Sorting**: Sort tables by various columns in ascending or descending order (`ORDER BY`).
-   **Data Aggregation and Analytics**: Perform complex analysis using `GROUP BY` with aggregate functions (`COUNT`, `AVG`, `SUM`, etc.) to generate insights like:
    -   Restaurant menu statistics (item count, average price).
    -   Customer spending habits.
    -   Order status summaries.
-   **Real-time SQL Query Display**: A unique UI component shows the generated SQL query for every database interaction, offering a powerful learning tool.
-   **Database Initialization**: A one-click utility to drop, create, and populate the entire database with a rich set of Indian-themed sample data.

---

## Technology Stack

| Component           | Technology / Library       |
| ------------------- | -------------------------- |
| **Backend Framework** | Flask                      |
| **Database**        | MySQL 8.0+                 |
| **Python Connector**  | `mysql-connector-python`   |
| **Frontend**        | HTML, CSS, Vanilla JavaScript |
| **Templating Engine** | Jinja2                     |

---

## Getting Started

Follow these steps to get the project running on your local machine.

### Prerequisites

-   Python 3.8 or newer
-   MySQL Server (Community Edition 8.0+ is recommended)


### 1. Clone the Repository

First, navigate to a directory where you want to store the project (e.g., your Desktop or a dedicated 'projects' folder). Then, clone the repository using Git.

```bash
# Navigate to a general-purpose folder, for example:
cd C:\Users\YourUsername\Desktop

# Clone the project repository
git clone https://github.com/jonahmichael/food_ordering_system.git

# Move into the newly created project directory
cd food_ordering_system
```

### 2. Install Dependencies

Install the necessary Python packages using pip.
```bash
pip install flask mysql-connector-python
```

### 3. Set Up the Database

This project comes with a SQL script (`setup_database.sql`) that creates the database, defines the schema, and populates it with sample data.

**Important:** Make sure your MySQL service is running before proceeding.

You can run the script from the MySQL command line:
```bash
# Log in to MySQL (you will be prompted for your root password)
mysql -u root -p

# In the MySQL prompt, run the setup script
source setup_database.sql;

# Exit the MySQL prompt
exit
```

### 4. Configure the Database Connection

Open the `app.py` file in your code editor and find the database connection block. **Update the `password`** with your MySQL root password.

```python
# app.py

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_mysql_password",  # <--- CHANGE THIS
        database="food_ordering_system"
    )
    return conn
```

### 5. Run the Flask Application

With the database ready and the connection configured, you can now run the web server.

```bash
python app.py
```

You should see output indicating that the server is running, typically on `http://127.0.0.1:5000`.

### 6. Access the Application

Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

You should now see the Food Ordering System interface, fully populated with data. Enjoy exploring its features!

---

## DBMS Concepts Demonstrated

This project serves as a practical demonstration of the following core DBMS concepts:

#### 1. Advanced `SELECT` Queries
-   **Filtering (`WHERE`)**: Used in search functionality with `LIKE` and in filters with `IN`.
-   **Sorting (`ORDER BY`)**: Used for dynamic sorting of table data by `ASC` or `DESC`.
-   **Joining Tables (`JOIN`)**: `LEFT JOIN` and `INNER JOIN` are used extensively to combine data from multiple tables (e.g., showing a menu item with its restaurant and category names).

#### 2. Data Aggregation (`GROUP BY`)
-   Used to group rows that have the same values into summary rows.
-   Paired with aggregate functions like `COUNT()`, `AVG()`, `SUM()`, `MIN()`, `MAX()` to provide analytical insights.
-   The `HAVING` clause is used to filter these groups (e.g., `HAVING order_count > 0`).

#### 3. Data Definition Language (DDL)
-   The `setup_database.sql` script shows the use of `CREATE TABLE` to define the entire database schema from scratch.

#### 4. Data Manipulation Language (DML)
-   **`INSERT`**: Creating new records in every table.
-   **`UPDATE`**: Modifying existing records.
-   **`DELETE`**: Removing records from the database.

#### 5. Database Design & Integrity
-   **Primary Keys**: Each table has a unique `AUTO_INCREMENT` primary key.
-   **Foreign Keys**: Enforce referential integrity between tables (e.g., linking an `Order` to a `Customer`).
-   **Constraints**: Use of `NOT NULL` and `UNIQUE` constraints to ensure data quality.
-   **Cascade Operations**: `ON DELETE CASCADE` is used to automatically delete dependent records (e.g., deleting an order also deletes its associated order items).

---

## Database Schema

The database consists of 7 interconnected tables. 
### CHECK THE ER DIAGRAM FOR REFERENCE
<img width="2725" height="2100" alt="Untitled diagram-2025-10-28-112642" src="https://github.com/user-attachments/assets/3c2c85e7-508b-4a2d-8905-4615b9119a1a" />

<details>
<summary>Click to view Database Schema SQL</summary>

```sql
-- Customers: Stores user information.
CREATE TABLE Customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password VARCHAR(255) NOT NULL,
    address TEXT
);

-- Restaurants: Stores restaurant details.
CREATE TABLE Restaurants (
    restaurant_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    phone_number VARCHAR(15),
    cuisine_type VARCHAR(50),
    rating DECIMAL(2,1)
);

-- Categories: Stores food categories (e.g., Appetizer, Main Course).
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Menu_Items: Stores individual food items.
CREATE TABLE Menu_Items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    restaurant_id INT,
    category_id INT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE SET NULL
);

-- Orders: Stores customer order information.
CREATE TABLE Orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    restaurant_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE
);

-- Deliveries: Tracks delivery status for each order.
CREATE TABLE Deliveries (
    delivery_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT UNIQUE,
    delivery_person_name VARCHAR(100),
    delivery_status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE
);

-- Order_Items: A junction table linking Orders to the Menu_Items they contain.
CREATE TABLE Order_Items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    item_id INT,
    quantity INT NOT NULL,
    item_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES Menu_Items(item_id) ON DELETE CASCADE
);
```
</details>

---

**Developed by Jonah Michael**
*B.Tech 2nd Year - DBMS Project*
