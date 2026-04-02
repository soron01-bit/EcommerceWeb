from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Review, Store
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
