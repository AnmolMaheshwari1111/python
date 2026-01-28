# Python & SQL Inventory/Billing System

A robust Command Line Interface (CLI) application for managing shop inventory, processing sales (billing), and tracking revenue. This system connects Python to a MySQL database to ensure data persistence and transaction safety.

## 🚀 Features

* **Billing System:** Create bills, view past bills, and edit bills (void & re-ring) with automatic stock adjustment.
* **Inventory Management:** Add new products, restock existing items, and delete obsolete products.
* **Stock Alerts:** Visual `⚠️` warnings when stock dips below a defined threshold.
* **Reporting:** View daily sales totals and revenue summaries.
* **Transaction Safety:** Uses ACID transactions (commit/rollback) to prevent data corruption during errors.

## 🛠️ Prerequisites

1.  **Python 3.x** installed.
2.  **MySQL Server** installed and running.
3.  **Python MySQL Connector** library.

### Installation

1.  Open your terminal/command prompt.
2.  Install the required library:
    ```bash
    pip install mysql-connector-python
    ```

#### If having this error

```Initializing System...

❌ Critical Database Error: Authentication plugin 'caching_sha2_password' is not supported
```
Put this code into MySQL Command Line Client or MySQL Workbench.

```ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
FLUSH PRIVILEGES;
```
This is a very common error when using MySQL 8.0 or newer.

MySQL 8.0 changed its default password mechanism to something called caching_sha2_password, but many Python connectors (or specific configurations) still expect the older method (mysql_native_password).

###Menu Options
1. New Bill (Sale): Select products by ID and enter quantity. The system auto-deducts stock and calculates totals.

3. Edit Bill: If a mistake is made, enter the Bill ID. The system restores the original stock and lets you re-enter the items correctly.

5. Add NEW Product: Enter details for entirely new items in your shop.

6. Update Product: Restock items (e.g., add +50 to existing stock) or change prices.

7. Delete Product: Remove items. Note: You cannot delete items that have been sold in previous bills (to preserve history).

8. Sales Reports: Check how much revenue you generated today.