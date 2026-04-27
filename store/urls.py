from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Legacy Admin Redirects
    path('admin-access/', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin-login/', RedirectView.as_view(url='/admin/login/', permanent=True)),
    path('admin-register/', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin-register/complete/', RedirectView.as_view(url='/admin/', permanent=True)),
    
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('buy/<int:pk>/', views.buy_product, name='buy_product'),
    path('profile/', views.user_profile, name='user_profile'),
    
    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Order URLs
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Store Management
    path('my-store/', views.my_store, name='my_store'),
    path('my-store/create/', views.create_store, name='create_store'),
    path('my-store/add-product/', views.add_product, name='add_product'),
    path('my-store/edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('my-store/delete-image/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    # Auth views
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
