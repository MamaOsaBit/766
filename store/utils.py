import json
from .models import *
from babel import numbers
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


def format_price(price):
    return numbers.format_decimal(price or 0, locale='es_CL')


def cookieCart(request):
    try:
        cart = json.loads(request.COOKIES.get('cart', '{}'))
    except json.JSONDecodeError:
        cart = {}

    items = []
    order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
    cartItems = 0

    for product_id, data in cart.items():
        try:
            quantity = data.get('quantity', 0)
            cartItems += quantity

            product = Product.objects.get(id=product_id)

            total = product.price * quantity
            order['get_cart_total'] += total
            order['get_cart_items'] += quantity

            item = {
                'id': product.id,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'formatted_price': format_price(product.price),
                    'imageURL': product.imageURL
                },
                'quantity': quantity,
                'digital': product.digital,
                'get_total': total,
                'formatted_total': format_price(total)
            }
            items.append(item)

            if not product.digital:
                order['shipping'] = True
        except Product.DoesNotExist:
            continue  # ignoramos productos inválidos

    order['formatted_cart_total'] = format_price(order['get_cart_total'])
    return {'cartItems': cartItems, 'order': order, 'items': items}


def cartData(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, _ = Order.objects.get_or_create(customer=customer, complete=False)

        items_data = []
        for item in order.orderitem_set.all():
            product = item.product

            # ✅ Si el producto fue eliminado, eliminamos el item del pedido
            if not product or not Product.objects.filter(id=product.id).exists():
                item.delete()
                continue

            item_data = {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'formatted_price': format_price(product.price),
                    'imageURL': product.imageURL
                },
                'quantity': item.quantity,
                'get_total': item.get_total,
                'formatted_total': format_price(item.get_total)
            }
            items_data.append(item_data)

        return {
            'cartItems': order.get_cart_items,
            'order': {
                'get_cart_total': order.get_cart_total,
                'get_cart_items': order.get_cart_items,
                'id': order.id,
                'formatted_cart_total': format_price(order.get_cart_total)
            },
            'items': items_data
        }

    else:
        return cookieCart(request)



def guestOrder(request, data):
    name = data['form']['name']
    email = data['form']['email']

    cookieData = cookieCart(request)
    items = cookieData['items']

    customer, _ = Customer.objects.get_or_create(email=email)
    customer.name = name
    customer.save()

    order = Order.objects.create(customer=customer, complete=False)

    for item in items:
        try:
            product = Product.objects.get(id=item['id'])
            OrderItem.objects.create(
                product=product,
                order=order,
                quantity=item['quantity']
            )
        except Product.DoesNotExist:
            continue  # ignoramos productos eliminados

    return customer, order