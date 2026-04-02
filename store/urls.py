from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('buy/<int:pk>/', views.buy_product, name='buy_product'),
    
    # Store Management
    path('my-store/', views.my_store, name='my_store'),
    path('my-store/create/', views.create_store, name='create_store'),
    path('my-store/add-product/', views.add_product, name='add_product'),
    # Auth views
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
