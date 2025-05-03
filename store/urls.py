from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
        #Leave as empty string for base url
	path('', views.store, name="store"),  #pagina principal
	path('cart/', views.cart, name="cart"),  #carrito de compras
	path('checkout/', views.checkout, name="checkout"),  #pago

	path('update_item/', views.updateItem, name="update_item"),  #actualiza el carrito de compras
	path('process_order/', views.processOrder, name="process_order"),  #procesa el pedido
    path('register/', views.register, name="register"),  #pagina de registro
    
	path('agregar/', views.add_product, name="agregar"),  #pagina de inicio de sesion
    path('listar/', views.list_product, name="listar"),  #pagina de inicio de sesion
    path('editar/<id>/', views.edit_product, name="editar"),  #pagina de inicio de sesion
    path('eliminar/<id>/', views.delete_product, name="eliminar"),  #pagina de inicio de sesion
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)