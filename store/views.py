from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth import login, authenticate
import json
import datetime
from . models import * 
from . utils import *
from babel import numbers
from . forms import *


def format_price(price):
    return numbers.format_decimal(price, locale='es_CL')

def store(request):
    # Obtener datos del carrito (tanto autenticados como no autenticados)
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Obtener productos de la base de datos y formatear precios
    products = Product.objects.all()
    for product in products:
        product.formatted_price = format_price(product.price)

    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)

def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Recorrer cada item y acceder de manera correcta dependiendo de si es un diccionario o un objeto
    for item in items:
        if isinstance(item['product'], dict):  # Si item['product'] es un diccionario (no autenticado)
            product = item['product']
        else:  # Si es un objeto Product (autenticado)
            product = item['product']

        product['formatted_price'] = format_price(product['price'])
        item['formatted_total'] = format_price(item['get_total'])

    # Formatear el total del carrito
    order['formatted_cart_total'] = format_price(order['get_cart_total'])

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    response = render(request, 'store/cart.html', context)

    # ✅ Si es usuario anónimo y se limpió el carrito, actualizamos la cookie
    if not request.user.is_authenticated and 'cleaned_cart' in data:
        response.set_cookie('cart', json.dumps(data['cleaned_cart']))

    return response



def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Formatear precios y totales para cada item
    for item in items:
        if isinstance(item['product'], dict):  # Si item['product'] es un diccionario (no autenticado)
            product = item['product']
        else:  # Si es un objeto Product (autenticado)
            product = item['product']

        product['formatted_price'] = format_price(product['price'])
        item['formatted_total'] = format_price(item['get_total'])

    order['formatted_cart_total'] = format_price(order['get_cart_total'])

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)



def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(
    user=request.user,
    defaults={
        'name': request.user.username,
        'email': request.user.email
    }
)
        product = Product.objects.get(id=productId)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            orderItem.quantity = (orderItem.quantity + 1)
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)

        orderItem.save()

        if orderItem.quantity <= 0:
            orderItem.delete()

        return JsonResponse('Item was added', safe=False)
    else:
        # Manejar carrito para usuarios no registrados usando cookies
        try:
            cart = json.loads(request.COOKIES['cart'])
        except:
            cart = {}

        if productId in cart:
            if action == 'add':
                cart[productId]['quantity'] += 1
            elif action == 'remove':
                cart[productId]['quantity'] -= 1

            if cart[productId]['quantity'] <= 0:
                del cart[productId]

            response = JsonResponse('Item was added', safe=False)
            response.set_cookie('cart', json.dumps(cart))  # Guardar cambios en las cookies
            return response

        return JsonResponse('Item not found', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer, created = Customer.objects.get_or_create(
    user=request.user,
    defaults={
        'name': request.user.username,
        'email': request.user.email
    }
)
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

def register(request):
    data = {
         'form': CustomerRegistrationForm()
    }

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request, user)
            messages.success(request, 'Registro exitoso')
            return redirect(to="store")
        data['form'] = form

    return render(request, 'registration/register.html', data)
    
def add_product(request):
    data = {
        'form': ProductForm()
    }

    if request.method == 'POST':
        form = ProductForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado exitosamente')
        else:
            messages.error(request, 'Error al agregar el producto')
            data['form'] = form

    return render(request, 'product/agregar.html', data)

def list_product(request):
    products = Product.objects.all()

    data = {
        'products': products,
        'form': ProductForm()
    }

    return render(request, 'product/listar.html', data)

def edit_product(request, id):
    
    product = get_object_or_404(Product, id=id)
    data = {
        'form': ProductForm(instance=product)
    }

    if request.method == 'POST':
        form = ProductForm(data=request.POST, files=request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto modificado exitosamente')
            return redirect(to="listar")
        else:
            messages.error(request, 'Error al modificar el producto')
            data['form'] = form

    return render(request, 'product/modificar.html', data)

def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect(to="listar")