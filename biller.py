import mysql.connector
from mysql.connector import Error
import sys
from datetime import datetime



whatsmypass = input("Enter Database Password: ")
# --- CONFIGURATION ---
DB_HOST = "localhost"
DB_USER = "root"          
DB_PASS = whatsmypass
DB_NAME = "shop_billing"

def create_database_and_tables():
    """Initial setup for database and tables."""
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.database = DB_NAME

        # Products Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                alert_threshold INT DEFAULT 5
            )
        """)

        # Bills Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100),
                bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                total_amount DECIMAL(10, 2) DEFAULT 0.00
            )
        """)

        # Bill Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bill_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bill_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                line_total DECIMAL(10, 2),
                FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # Dummy Data check
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            print("Populating dummy data...")
            sql = "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)"
            val = [('Nothing', 9.99, 1)]
            cursor.executemany(sql, val)
            conn.commit()

        cursor.close()
        conn.close()

    except Error as e:
        print(f"❌ Critical Database Error: {e}")
        sys.exit(1)

class BillingSystem:
    def __init__(self):
        self.conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        self.cursor = self.conn.cursor(dictionary=True)

    # --- REPORTING FEATURE ---
    def generate_report(self):
        print("\n--- SALES REPORTS ---")
        print("1. Today's Total Sales")
        print("2. List All Bills")
        
        choice = input("Select Report Type: ")

        if choice == '1':
            # Calculate sum of all bills created TODAY
            # DATE(bill_date) extracts just the YYYY-MM-DD part to compare
            query = "SELECT COUNT(*) as count, SUM(total_amount) as total FROM bills WHERE DATE(bill_date) = CURDATE()"
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            # Handle case where no sales made
            count = result['count'] if result else 0
            total = result['total'] if result['total'] else 0.00
            
            print(f"\n📊 REPORT: {datetime.now().strftime('%Y-%m-%d')}")
            print(f"   Bills Generated: {count}")
            print(f"   Total Revenue:   ${total}")

        elif choice == '2':
            self.cursor.execute("SELECT * FROM bills ORDER BY bill_id DESC")
            bills = self.cursor.fetchall()
            print(f"\n{'ID':<5} {'Date':<20} {'Customer':<20} {'Total':<10}")
            print("-" * 60)
            for b in bills:
                print(f"{b['bill_id']:<5} {b['bill_date'].strftime('%Y-%m-%d %H:%M'):<20} {b['customer_name']:<20} ${b['total_amount']:<10}")
            print("-" * 60)
        else:
            print("Invalid choice.")

    # --- INVENTORY MANAGEMENT ---
    def delete_product(self):
        print("\n--- DELETE PRODUCT ---")
        self.show_products()
        try:
            p_id = int(input("Enter Product ID to DELETE: "))
            
            # 1. Check if product exists
            self.cursor.execute("SELECT name FROM products WHERE product_id = %s", (p_id,))
            prod = self.cursor.fetchone()
            if not prod:
                print("❌ Product not found.")
                return

            confirm = input(f"⚠️ Are you sure you want to delete '{prod['name']}'? (y/n): ")
            if confirm.lower() != 'y':
                print("Deletion cancelled.")
                return

            # 2. Try to Delete
            try:
                self.cursor.execute("DELETE FROM products WHERE product_id = %s", (p_id,))
                self.conn.commit()
                print(f"✅ Deleted '{prod['name']}' successfully.")
            except mysql.connector.errors.IntegrityError as e:
                # Error 1451 is "Cannot delete or update a parent row: a foreign key constraint fails"
                if e.errno == 1451:
                    print(f"\n❌ CANNOT DELETE: This product is part of past bill records.")
                    print("   Suggestion: Use 'Update Product' to set Stock to 0 instead.")
                else:
                    print(f"❌ Database Error: {e}")

        except ValueError:
            print("Invalid input.")

    def add_new_product(self):
        print("\n--- ADD NEW PRODUCT ---")
        try:
            name = input("Product Name: ")
            price = float(input("Price: "))
            stock = int(input("Initial Stock: "))
            threshold = int(input("Alert Threshold (Default 5): ") or 5)

            query = "INSERT INTO products (name, price, stock, alert_threshold) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(query, (name, price, stock, threshold))
            self.conn.commit()
            print(f"✅ Added '{name}' successfully!")
        except mysql.connector.Error as err:
            print(f"❌ Error: {err}")
        except ValueError:
            print("❌ Invalid input.")

    def update_product_inventory(self):
        print("\n--- UPDATE EXISTING PRODUCT ---")
        self.show_products()
        try:
            p_id = int(input("Enter Product ID to update: "))
            self.cursor.execute("SELECT * FROM products WHERE product_id = %s", (p_id,))
            prod = self.cursor.fetchone()
            if not prod:
                print("❌ Product not found.")
                return

            print(f"Selected: {prod['name']} | Current Price: ${prod['price']} | Current Stock: {prod['stock']}")
            print("Leave field blank to keep current value.")

            new_price = input(f"New Price [{prod['price']}]: ")
            new_stock = input(f"Add Stock (Quantity to ADD): ")
            new_threshold = input(f"New Alert Threshold [{prod['alert_threshold']}]: ")

            if new_price:
                self.cursor.execute("UPDATE products SET price = %s WHERE product_id = %s", (float(new_price), p_id))
            if new_stock:
                updated_stock = prod['stock'] + int(new_stock)
                self.cursor.execute("UPDATE products SET stock = %s WHERE product_id = %s", (updated_stock, p_id))
            if new_threshold:
                self.cursor.execute("UPDATE products SET alert_threshold = %s WHERE product_id = %s", (int(new_threshold), p_id))

            self.conn.commit()
            print("✅ Product updated successfully!")

        except ValueError:
            print("❌ Invalid input.")

    def show_products(self):
        self.cursor.execute("SELECT * FROM products")
        items = self.cursor.fetchall()
        print("\n--- INVENTORY LIST ---")
        print(f"{'ID':<5} {'Name':<20} {'Price':<10} {'Stock':<10} {'Alert At':<10}")
        print("-" * 60)
        for item in items:
            alert_mark = "⚠️" if item['stock'] <= item['alert_threshold'] else ""
            print(f"{item['product_id']:<5} {item['name']:<20} ${item['price']:<9} {item['stock']:<10} {item['alert_threshold']:<5} {alert_mark}")
        print("-" * 60)

    # --- BILLING FUNCTIONS ---
    def create_bill(self):
        print("\n--- NEW BILL ---")
        customer = input("Enter Customer Name: ")
        cart = []
        
        while True:
            self.show_products()
            try:
                p_id = int(input("Enter Product ID (0 to finish): "))
                if p_id == 0: break
                
                self.cursor.execute("SELECT name FROM products WHERE product_id = %s", (p_id,))
                if not self.cursor.fetchone():
                    print("❌ Invalid Product ID")
                    continue

                qty = int(input("Enter Quantity: "))
                cart.append({'product_id': p_id, 'qty': qty})
            except ValueError:
                print("Invalid input.")

        if not cart: return

        try:
            total_amt = 0
            self.cursor.execute("INSERT INTO bills (customer_name, total_amount) VALUES (%s, 0)", (customer,))
            bill_id = self.cursor.lastrowid

            for item in cart:
                self.cursor.execute("SELECT price, stock, name, alert_threshold FROM products WHERE product_id = %s", (item['product_id'],))
                prod = self.cursor.fetchone()
                
                if prod['stock'] < item['qty']: raise Exception(f"Not enough stock for {prod['name']}")

                line_total = prod['price'] * item['qty']
                total_amt += line_total
                
                new_stock = prod['stock'] - item['qty']
                self.cursor.execute("UPDATE products SET stock = %s WHERE product_id = %s", (new_stock, item['product_id']))

                self.cursor.execute(
                    "INSERT INTO bill_items (bill_id, product_id, quantity, line_total) VALUES (%s, %s, %s, %s)",
                    (bill_id, item['product_id'], item['qty'], line_total)
                )

                if new_stock <= prod['alert_threshold']:
                    print(f"⚠️  ALERT: Low Stock for {prod['name']}!")

            self.cursor.execute("UPDATE bills SET total_amount = %s WHERE bill_id = %s", (total_amt, bill_id))
            self.conn.commit()
            print(f"✅ Bill #{bill_id} Saved! Total: ${total_amt}")

        except Exception as e:
            self.conn.rollback()
            print(f"❌ Transaction Failed: {e}")

    def view_bill(self):
        try:
            b_id = int(input("\nEnter Bill ID to view: "))
            self.cursor.execute("SELECT * FROM bills WHERE bill_id = %s", (b_id,))
            bill = self.cursor.fetchone()
            if not bill:
                print("Bill not found.")
                return

            print(f"\n--- BILL #{b_id} ---")
            print(f"Customer: {bill['customer_name']} | Date: {bill['bill_date']}")
            
            self.cursor.execute("""
                SELECT p.name, bi.quantity, bi.line_total 
                FROM bill_items bi 
                JOIN products p ON bi.product_id = p.product_id 
                WHERE bi.bill_id = %s
            """, (b_id,))
            
            for i in self.cursor.fetchall():
                print(f"{i['name']:<20} x {i['quantity']:<3} = ${i['line_total']}")
            print(f"TOTAL: ${bill['total_amount']}")
        except ValueError: print("Invalid ID.")

    def edit_bill(self):
        print("\n--- EDIT BILL ---")
        try:
            b_id = int(input("Enter Bill ID to Edit: "))
            self.cursor.execute("SELECT * FROM bills WHERE bill_id = %s", (b_id,))
            if not self.cursor.fetchone():
                print("Bill not found.")
                return

            self.cursor.execute("SELECT product_id, quantity FROM bill_items WHERE bill_id = %s", (b_id,))
            for item in self.cursor.fetchall():
                self.cursor.execute("UPDATE products SET stock = stock + %s WHERE product_id = %s", (item['quantity'], item['product_id']))
            
            self.cursor.execute("DELETE FROM bill_items WHERE bill_id = %s", (b_id,))

            print("Previous items cleared. Enter NEW items:")
            cart = []
            while True:
                self.show_products()
                p_id = int(input("Enter Product ID (0 to finish): "))
                if p_id == 0: break
                qty = int(input("Enter Quantity: "))
                cart.append({'product_id': p_id, 'qty': qty})
            
            if not cart:
                self.conn.rollback()
                return

            total = 0
            for item in cart:
                self.cursor.execute("SELECT price, stock FROM products WHERE product_id = %s", (item['product_id'],))
                prod = self.cursor.fetchone()
                if prod['stock'] < item['qty']: raise Exception("Insufficient stock")
                
                line_total = prod['price'] * item['qty']
                total += line_total
                
                self.cursor.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (item['qty'], item['product_id']))
                self.cursor.execute("INSERT INTO bill_items (bill_id, product_id, quantity, line_total) VALUES (%s, %s, %s, %s)", (b_id, item['product_id'], item['qty'], line_total))

            self.cursor.execute("UPDATE bills SET total_amount = %s WHERE bill_id = %s", (total, b_id))
            self.conn.commit()
            print("✅ Bill Updated!")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Edit Failed: {e}")

# --- MAIN MENU ---
if __name__ == "__main__":
    create_database_and_tables()
    app = BillingSystem()
    
    while True:
        print("\n=== INVENTORY & BILLING SYSTEM ===")
        print("1. New Bill (Sale)")
        print("2. View Bill")
        print("3. Edit Bill (Return/Exchange)")
        print("4. Check Inventory List")
        print("5. Add NEW Product")
        print("6. Update Product (Restock)")
        print("7. DELETE Product")
        print("8. Sales Reports 📊")
        print("9. Exit")
        
        choice = input("Select Option: ")
        
        if choice == '1': app.create_bill()
        elif choice == '2': app.view_bill()
        elif choice == '3': app.edit_bill()
        elif choice == '4': app.show_products()
        elif choice == '5': app.add_new_product()
        elif choice == '6': app.update_product_inventory()
        elif choice == '7': app.delete_product()
        elif choice == '8': app.generate_report()
        elif choice == '9': break
        else: print("Invalid choice.")