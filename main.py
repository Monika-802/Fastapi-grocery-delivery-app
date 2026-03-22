from fastapi import FastAPI, Query, Response, status, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)
    delivery_slot:  str = 'Morning' 
    bulk_order: bool = False

class NewItem(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    unit: str = Field(..., in_length=2)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)
    delivery_slot: str="morning"

items = [
    {"id": 1, "name": "Apples", "price": 120, "unit": "kg", "category": "Fruit", "in_stock": True},
    {"id": 2, "name": "Milk", "price": 60, "unit": "litre", "category": "Dairy", "in_stock": False},
    {"id": 3, "name": "Rice", "price": 80, "unit": "kg", "category": "Grain", "in_stock": True},
    {"id": 4, "name": "Spinach", "price": 30, "unit": "piece", "category": "Vegetable", "in_stock": False},
    {"id": 5, "name": "Eggs", "price": 70, "unit": "dozen", "category": "Dairy", "in_stock": True},
    {"id": 6, "name": "Bananas", "price": 50, "unit": "dozen", "category": "Fruit", "in_stock": True},
]


orders = []
order_counter = 1
cart = []

def find_item(item_id: int):
    for i in items:
        if i['id'] == item_id:
            return i
    return None

def calculate_total(item: dict, quantity: int) -> int:
    return item['price'] * quantity

def filter_items_logic(category=None, min_price=None, max_price=None, unit=None, in_stock=None):
    result = items
    if category is not None:
        result = [i for i in result if i['category'] == category]
    if min_price is not None:
        result = [i for i in result if i['price'] >= min_price]
    if max_price is not None:
        result = [i for i in result if i['price'] <= max_price]
    if unit is not None:
        result = [i for i in result if i['unit'] == unit]
    if in_stock is not None:
        result = [i for i in result if i['in_stock'] == in_stock]
    return result

def calculate_order_total(price, quantity, delivery_slot, bulk_order):
    original_total = price * quantity
    discounted_total = original_total
    if bulk_order and quantity >= 10:
        discounted_total = original_total * 0.92
    if delivery_slot == "Morning":
        delivery_charge = 40
    elif delivery_slot == "Evening":
        delivery_charge = 60
    else:
        delivery_charge = 0
    final_total = discounted_total + delivery_charge
    return {
        "original_amount": int(original_total),
        "discounted_amount": int(discounted_total),
        "delivery_charge": delivery_charge,
        "final_total": int(final_total)
    }

@app.get('/')
def home():
    return {'message': 'Welcome to Grocery API'}

@app.get('/items')
def get_all_items():
    return {'items': items, 'total': len(items)}

@app.get('/items/filter')
def filter_items(category: str = Query(None), min_price: int = Query(None), max_price: int = Query(None), unit:str = Query(None), in_stock: bool = Query(None)):
    result = filter_items_logic(category, min_price, max_price, unit, in_stock)
    return {'filtered_items': result, 'count': len(result)}

@app.get('/items/search')
def search_items(keyword: str = Query(...)):
    results = [i for i in items if keyword.lower() in i['name'].lower()or keyword.lower() in i['category'].lower()]
    if not results:
        return {'message': f'No items found for: {keyword}', 'results': []}
    return {'keyword': keyword, 'total_found': len(results), 'results': results}

@app.get('/items/sort')
def sort_items(sort_by: str = Query('price'), order: str = Query('asc')):
    sorted_list = sorted(items, key=lambda x: x[sort_by], reverse=(order == 'desc'))
    return {'sort_by': sort_by, 'order': order, 'total_items': len(sorted_list),'items': sorted_list}

@app.get('/items/page')
def get_items_paged(page: int = Query(1, ge=1), limit: int = Query(4, ge=1)):
    total = len(items)
    total_pages = total/limit
    start = (page - 1) * limit
    end = start + limit
    paged = items[start:end]
    return {'page': page, 'total_pages': total_pages,'limit': limit, 'total': len(items), 'products': paged}

@app.get("/items/browse")
def browse_items(
    keyword: str = None,
    category: str = None,
    in_stock: bool = None,
    sort_by: str = "id",
    order: str = "asc",
    page: int = 1,
    limit: int = 1
):
    results = items
    if keyword:
        results = [i for i in results if keyword.lower() in i["name"].lower()]
    if category:
        results = [i for i in results if i["category"].lower() == category.lower()]
    if in_stock is not None:
        results = [i for i in results if i["in_stock"] == in_stock]
    results.sort(key=lambda x: x.get(sort_by, ""), reverse=(order=="desc"))
    start, end = (page-1)*limit, page*limit
    return {"total": len(results), "page": page, "limit": limit, "results": results[start:end]}

@app.post('/items')
def add_item(new_item: NewItem, response: Response):
    for i in items:
        if i["name"].lower() == new_item.name.lower():
            raise HTTPException(status_code=400, detail="Item already exists")

    next_id = max([i['id'] for i in items], default=0) + 1

    item = {
        'id': next_id,
        'name': new_item.name,
        'price': new_item.price,
        'unit': new_item.unit,
        'category': new_item.category,
        'in_stock': new_item.in_stock
    }

    items.append(item)
    response.status_code = status.HTTP_201_CREATED

    return {'message': 'Item added', 'item': item}


@app.get('/items/summary')
def items_summary():
    total_items = len(items)
    in_stock_count = sum(1 for i in items if i['in_stock'])
    out_of_stock_count = total_items - in_stock_count

    category_breakdown = {}
    for i in items:
        category = i['category']
        category_breakdown[category] = category_breakdown.get(category, 0) + 1

    return {
        "total_items": total_items,
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "category_breakdown": category_breakdown
    }

@app.get('/items/{item_id}')
def get_item(item_id: int):
    item = find_item(item_id)
    if not item:
        return {'error': 'Item not found'}
    return {'item': item}

@app.put('/items/{item_id}')
def update_item(item_id: int, response: Response, in_stock: bool = Query(None), price: int = Query(None)):
    item = find_item(item_id)
    if not item:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Item not found'}
    if in_stock is not None:
        item['in_stock'] = in_stock
    if price is not None:
        item['price'] = price
    return {'message': 'Item updated', 'item': item}

@app.delete('/items/{item_id}')
def delete_item(item_id: int, response: Response):
    item = find_item(item_id)
    if not item:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Item not found'}
    items.remove(item)
    return {'message': f"{item['name']} deleted"}

@app.post('/orders/place')
def place_order(order_data: OrderRequest, delivery_slot: str):
    global order_counter
    
    item = find_item(order_data.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not item['in_stock']:
        return {'error': 'item is out of stock'}
    
    total_cost = calculate_order_total(item['price'], order_data.quantity, delivery_slot, order_data.bulk_order)
    
    order_status = "confirmed"
    new_order = {
        'order_id': order_counter,
        'customer_name': order_data.customer_name,
        'item_name': item['name'],
        'quantity': order_data.quantity,
        'unit': item.get('unit', 'unit'),
        'delivery_slot': delivery_slot,
        'delivery_address': order_data.delivery_address,
        "bulk_order": order_data.bulk_order,
        'total_cost': total_cost,
        'order_status': order_status
    }
    
    orders.append(new_order)
    order_counter += 1
    
    return {
        'message': 'Order placed successfully', 
        'order': new_order
    }

@app.post("/orders/create")
def create_order(order: OrderRequest):
    item = find_item(order.item_id)
    if not item:
        return {"error": "Item not found"}
    if not item["in_stock"]:
        return {"error": "Item out of stock"}

    amounts = calculate_order_total(
        item["price"],
        order.quantity,
        order.delivery_slot,
        order.bulk_order
    )

    return {
        "customer_name": order.customer_name,
        "item_name": item["name"],
        "quantity": order.quantity,
        "delivery_slot": order.delivery_slot,
        "bulk_order": order.bulk_order,
        "amounts": amounts
    }

@app.get('/orders/sort')
def sort_orders(order: str = Query("asc")):
    reverse = order.lower() == "desc"
    sorted_list = sorted(orders, key=lambda x: x.get("total_cost", 0), reverse=reverse)
    return {"order": order, "total_orders": len(sorted_list), "orders": sorted_list}


@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    results = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}


@app.get('/orders/page')
def get_orders_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(2, ge=1, le=20)
):
    start = (page - 1) * limit
    end = start + limit
    paged_orders = orders[start:end]

    return {
        "page": page,
        "limit": limit,
        "total_orders": len(orders),
        "total_pages": (len(orders) + limit - 1) // limit,
        "orders": paged_orders
    }

@app.get('/orders')
def get_all_orders():
    if not orders:
        return {'message': 'no new order added'}
    return {'orders': orders, 'grand_total': len(orders)}


@app.post('/cart/add')
def add_to_cart(item_id: int = Query(...), quantity: int = Query(1)):
    item = find_item(item_id)
    if not item:
        return {"error": "Item not found"}
    if not item["in_stock"]:
        return {"error": "Item out of stock"}

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            c["subtotal"] = calculate_total(item, c["quantity"])
            return {"message": "Cart updated", "cart_item": c}

    cart_item = {
        "item_id": item_id,
        "name": item["name"],
        "quantity": quantity,
        "price": item["price"],
        "subtotal": calculate_total(item, quantity)
    }

    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}

@app.get("/cart")
def get_cart():
    if not cart:
        return {"message": "Cart is empty", "items": [], "grand_total": 0}

    grand_total = 0
    updated_cart = []

    for item in cart:
        subtotal = item["price"] * item["quantity"]
        item["subtotal"] = subtotal
        grand_total += subtotal
        updated_cart.append(item)

    return {
        "items": updated_cart,
        "grand_total": grand_total
    }
    

@app.get('/cart')
def view_cart():
    return {'items': cart, 'total': sum(i['subtotal'] for i in cart)}

@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):
    for i, c in enumerate(cart):
        if c["item_id"] == item_id:
            removed = cart.pop(i)
            return {"message": "Item removed", "item": removed}
    raise HTTPException(status_code=404, detail="Item not found in cart")

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    placed_orders = []
    grand_total = 0

    for c in cart:
        order = {
            "order_id": len(orders) + 1,
            "customer_name": data.customer_name,
            "delivery_address": data.delivery_address,
            "delivery_slot": data.delivery_slot,
            "item_id": c["item_id"],
            "item_name": c["name"],
            "quantity": c["quantity"],
            "unit_price": c["price"],
            "subtotal": c["subtotal"],
            "status": "confirmed"
        }
        orders.append(order)
        placed_orders.append(order)
        grand_total += c["subtotal"]

    cart.clear()

    return {
        "message": "Checkout successful",
        "orders": placed_orders,
        "grand_total": grand_total
    }