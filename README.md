# Fastapi-grocery-delivery-app
A simple Grocery Store API built with FastAPI to manage items, orders, and shopping carts. It demonstrates CRUD operations, filtering, sorting, pagination, and checkout logic.
## Features
Item Management: Add, update, delete, and fetch items.
Filtering & Searching: Filter items by category, price, unit, stock; search by keyword.
Sorting & Pagination: Sort items/orders and paginate results.
Orders: Place, create, search, sort, and paginate orders.
Shopping Cart: Add/remove items, view cart, and checkout with delivery options.
Pricing Logic: Supports bulk discounts and delivery charges.
## Data 
Item: id, name, price, unit, category, in_stock
Order: order_id, customer_name, item_name, quantity, delivery_slot, total_cost, bulk_order
Cart: item_id, name, quantity, subtotal
## Technologies
Python 3.11
FastAPI
Pydantic for data validation
Usage
## Run the app:
using Command Prompt
uvicorn main:app --reload
Open docs at http://127.0.0.1:8000/docs⁠
Test API endpoints interactively.
