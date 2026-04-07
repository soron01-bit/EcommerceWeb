from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Review, Store, Cart, CartItem
from .forms import CustomUserCreationForm, ReviewForm, StoreForm, ProductForm

def home(request):
    products = Product.objects.all()
    return render(request, 'store/index.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    
    try:
        certificate = product.certificate
    except Exception:
        certificate = None
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to leave a review.')
            return redirect('login')
            
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('product_detail', pk=pk)
    else:
        form = ReviewForm()
        
    return render(request, 'store/product_detail.html', {
        'product': product,
        'certificate': certificate,
        'reviews': reviews,
        'form': form,
    })

@login_required
def buy_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Dummy logic to handle buying product
    messages.success(request, f'You have successfully purchased {product.name}!')
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})

@login_required
def my_store(request):
    try:
        store = request.user.store
        products = store.products.all()
        return render(request, 'store/my_store.html', {'store': store, 'products': products})
    except Store.DoesNotExist:
        return redirect('create_store')

@login_required
def create_store(request):
    if hasattr(request.user, 'store'):
        return redirect('my_store')
    
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.owner = request.user
            store.save()
            messages.success(request, 'Store created successfully!')
            return redirect('my_store')
    else:
        form = StoreForm()
    return render(request, 'store/create_store.html', {'form': form})

@login_required
def add_product(request):
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You must create a store first.')
        return redirect('create_store')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('my_store')
    else:
        form = ProductForm()
    return render(request, 'store/add_product.html', {'form': form})

# Edit product view
from django.http import HttpResponseForbidden
@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.store.owner != request.user:
        return HttpResponseForbidden("You are not allowed to edit this product.")
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('my_store')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/edit_product.html', {'form': form, 'product': product})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Get or create cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get quantity from POST request
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if product already in cart
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not item_created:
        # If already in cart, increase quantity
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('product_detail', pk=pk)

@login_required
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        total_price = cart.get_total_price()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
        total_price = 0
    
    return render(request, 'store/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    })

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated.')
    
    return redirect('view_cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart.')
    return redirect('view_cart')
