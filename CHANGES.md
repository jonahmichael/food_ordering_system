### Summary of Technical Changes

#### Backend (`app.py`)

1.  **Session-Based SQL Logging:**
    *   Flask's `session` has been implemented to store the last executed SQL query and its parameters.
    *   A helper function was created to format and log the SQL command and its arguments to the session object before every database call.
    *   This logging mechanism has been integrated into all routes that perform CRUD operations (`INSERT`, `UPDATE`, `DELETE`, `SELECT`).

2.  **Sensitive Data Masking:**
    *   The SQL logging function includes logic to identify and mask sensitive data, such as passwords, replacing them with `****` before saving the query to the session for display.

3.  **Dummy Data Overhaul:**
    *   The `init_db` function, which populates the database, was rewritten to use a new, extensive dataset. The prices in this dataset are now integers/floats representing Indian Rupees (₹).

4.  **Security Maintenance:**
    *   Despite displaying the SQL queries, the application continues to use parameterized queries (`mysql-connector`'s argument substitution) for all database operations to prevent SQL injection vulnerabilities.

#### Frontend (HTML & CSS in `templates/`)

1.  **SQL Query Display Component:**
    *   A new HTML `<div>` element has been added to the main template. It is styled with CSS to be fixed to the bottom-right of the viewport.
    *   This component dynamically renders the SQL query string stored in the Flask `session`.
    *   CSS styling includes a dark theme, monospace font (`Courier New`), and appropriate padding for readability.

2.  **CSS Refactoring and Overhaul:**
    *   The entire stylesheet was refactored to a minimalistic, light-themed design using a professional color palette (`#2c3e50`, `#f5f5f5`).
    *   All inline styles for status badges have been replaced with dedicated CSS classes (e.g., `.status-delivered`, `.status-pending`) for better maintainability and consistency.
    *   CSS transitions and hover effects were added to interactive elements, such as the watermark.

3.  **HTML Structure Updates:**
    *   The watermark element was changed from static text to an anchor tag (`<a>`) with `target="_blank"` to open a link in a new tab.
    *   All hardcoded currency symbols in the Jinja2 templates were changed from `$` to `₹`.
    *   All emoji characters were removed from the HTML templates to align with the new design.

#### Files Modified

*   **`app.py`**: Heavily modified to implement session management, the SQL logging feature, and to update the seed data.
*   **`templates/index.html`** (or a base layout template): Underwent a complete HTML and CSS overhaul to implement the new design, status badges, and the SQL query display box.
