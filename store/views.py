from decimal import Decimal
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import re
import unicodedata
from .models import Product, Review, Store, Cart, CartItem, ProductImage, UserProfile, Order
from .forms import (
    CustomUserCreationForm,
    ReviewForm,
    UserProfileForm,
    BuyNowForm,
    CartCheckoutForm,
)


SEARCH_SYNONYMS = {
    'phone': {'mobile', 'smartphone', 'cellphone', 'handset'},
    'mobile': {'phone', 'smartphone', 'cellphone', 'handset'},
    'cloths': {'clothes', 'clothing', 'dress', 'shirt', 'pant', 'jeans', 'tshirt'},
    'clothes': {'cloths', 'clothing', 'dress', 'shirt', 'pant', 'jeans', 'tshirt'},
    'clothing': {'cloths', 'clothes', 'dress', 'shirt', 'pant', 'jeans', 'tshirt'},
    'shirt': {'tshirt', 't', 'tee', 'tshirt'},
    'tshirt': {'shirt', 'tee', 't shirt'},
    'laptop': {'notebook', 'pc', 'computer'},
    'bike': {'motorcycle', 'motorbike'},
    'computer': {'pc', 'desktop', 'laptop'},
    'pc': {'computer', 'desktop', 'laptop'},
    'keyboard': {'key board', 'keybord'},
    'keybord': {'keyboard', 'key board'},
}

SHORT_TECH_TOKENS = {'pc', 'tv', 'ac', 'vr', 'cpu', 'gpu', 'ssd', 'hdd', 'ram'}

DOMAIN_KEYWORDS = {
    'clothing': {
        'cloths', 'clothes', 'clothing', 'shirt', 'tshirt', 'tee', 'pant',
        'pants', 'jeans', 'dress', 'jacket', 'shorts', 'hoodie', 'kurta',
        'saree', 'shoe', 'shoes'
    },
    'electronics': {
        'electrical', 'electronics', 'electronic', 'phone', 'mobile', 'smartphone',
        'laptop', 'pc', 'computer', 'keyboard', 'mouse', 'monitor', 'tablet',
        'charger', 'earbuds', 'headphone', 'tv', 'camera', 'motherboard',
        'cpu', 'gpu', 'ssd', 'hdd', 'ram'
    },
    'vehicles': {
        'bike', 'bikes', 'motorbike', 'motorcycle', 'car', 'cars', 'scooter',
        'vehicle', 'vehicles'
    },
}

INTENT_PROFILES = {
    'clothing': {
        'cloths', 'clothes', 'clothing', 'shirt', 'tshirt', 'tee', 'pant', 'pants',
        'jeans', 'dress', 'jacket', 'shorts', 'hoodie', 'kurta', 'saree', 'shoe', 'shoes'
    },
    'electronics': {
        'electrical', 'electronics', 'electronic', 'phone', 'mobile', 'smartphone',
        'laptop', 'pc', 'computer', 'keyboard', 'mouse', 'monitor', 'tablet', 'charger',
        'earbuds', 'headphone', 'tv', 'camera', 'motherboard', 'cpu', 'gpu', 'ssd', 'hdd', 'ram'
    },
    'vehicles': {
        'bike', 'bikes', 'motorbike', 'motorcycle', 'car', 'cars', 'scooter', 'vehicle', 'vehicles'
    },
}

INTENT_TO_DOMAIN = {
    'clothing': 'clothing',
    'electronics': 'electronics',
    'vehicles': 'vehicles',
}

SHOE_SIZE_CHOICES = [(str(size), str(size)) for size in range(1, 11)]
APPAREL_SIZE_CHOICES = [
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
    ('XL', 'XL'),
    ('XXL', 'XXL'),
]
DEFAULT_SIZE_CHOICES = [('ONE_SIZE', 'One Size')]
SHOE_SIZE_KEYWORDS = {
    'shoe', 'shoes', 'sneaker', 'sneakers', 'boot', 'boots', 'sandal', 'sandals',
    'loafer', 'loafers', 'slipper', 'slippers', 'footwear',
}
APPAREL_SIZE_KEYWORDS = {
    'shirt', 'tshirt', 't shirt', 'tee', 'pant', 'pants', 'trouser', 'trousers',
    'jeans', 'jacket', 'hoodie', 'dress', 'top', 'kurta', 'skirt', 'shorts', 'sweater',
}


def normalize_text(value):
    # Normalize to lowercase ascii-like text and remove punctuation for robust matching.
    normalized = unicodedata.normalize('NFKD', str(value or ''))
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', ascii_text.lower())
    return re.sub(r'\s+', ' ', cleaned).strip()


def expand_query_tokens(tokens):
    expanded = set()
    for token in tokens:
        token_normalized = normalize_text(token)
        if not token_normalized:
            continue

        expanded.add(token_normalized)

        if token_normalized.endswith('s') and len(token_normalized) > 3:
            expanded.add(token_normalized[:-1])

        for synonym in SEARCH_SYNONYMS.get(token_normalized, set()):
            synonym_normalized = normalize_text(synonym)
            if synonym_normalized:
                expanded.add(synonym_normalized)

    return sorted(expanded)


def get_word_set(text):
    return {word for word in normalize_text(text).split() if word}


def matches_any_keyword(text, keywords):
    normalized_text = normalize_text(text)
    return any(keyword in normalized_text for keyword in keywords)


def get_product_size_choices(product):
    size_type = getattr(product, 'size_type', Product.SIZE_TYPE_ONE_SIZE)

    if size_type == Product.SIZE_TYPE_SHOE:
        return SHOE_SIZE_CHOICES

    if size_type == Product.SIZE_TYPE_APPAREL:
        return APPAREL_SIZE_CHOICES

    return DEFAULT_SIZE_CHOICES


def levenshtein_distance(left, right):
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    if len(left) < len(right):
        left, right = right, left

    previous_row = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current_row = [i]
        for j, right_char in enumerate(right, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            replace_cost = previous_row[j - 1] + (left_char != right_char)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_similarity(left, right):
    left = normalize_text(left)
    right = normalize_text(right)

    if not left or not right:
        return 0.0

    max_len = max(len(left), len(right))
    if max_len == 0:
        return 1.0

    distance = levenshtein_distance(left, right)
    return max(0.0, 1.0 - (distance / max_len))


def best_token_similarity(token, words):
    if not token or not words:
        return 0.0

    token = normalize_text(token)
    best = 0.0
    for word in words:
        if abs(len(word) - len(token)) > max(3, len(token) // 2):
            continue
        similarity = levenshtein_similarity(token, word)
        if similarity > best:
            best = similarity
    return best


def detect_search_intent_ai(query_normalized, query_tokens):
    # Lightweight AI-style intent detector using typo-tolerant similarity to intent profiles.
    intent_scores = {intent: 0.0 for intent in INTENT_PROFILES}
    corrected_tokens = set(query_tokens)
    query_words = set(query_tokens) | get_word_set(query_normalized)

    for token in query_words:
        token = normalize_text(token)
        if not token:
            continue

        best_intent = None
        best_keyword = None
        best_similarity = 0.0

        for intent, keywords in INTENT_PROFILES.items():
            if token in keywords:
                intent_scores[intent] += 1.3
                if 1.0 > best_similarity:
                    best_intent = intent
                    best_keyword = token
                    best_similarity = 1.0
                continue

            similarity = best_token_similarity(token, keywords)
            if similarity > best_similarity:
                best_similarity = similarity
                best_intent = intent

                if similarity >= 0.70:
                    best_keyword = max(
                        keywords,
                        key=lambda keyword: levenshtein_similarity(token, keyword),
                    )

        if best_intent and best_similarity >= 0.60:
            intent_scores[best_intent] += best_similarity

        if best_keyword and best_similarity >= 0.78:
            corrected_tokens.add(best_keyword)

    best_intent = max(intent_scores, key=intent_scores.get)
    best_score = intent_scores[best_intent]
    second_score = max(
        (score for intent, score in intent_scores.items() if intent != best_intent),
        default=0.0,
    )

    confidence = best_score - second_score
    confident = best_score >= 1.3 and confidence >= 0.4

    return {
        'intent': best_intent,
        'intent_score': best_score,
        'confidence_gap': confidence,
        'confident': confident,
        'expanded_tokens': sorted(corrected_tokens),
    }


def build_search_tokens(query_normalized):
    raw_tokens = [token for token in query_normalized.split() if token]
    filtered_tokens = [
        token
        for token in raw_tokens
        if len(token) >= 3 or token in SHORT_TECH_TOKENS
    ]
    if not filtered_tokens and query_normalized:
        filtered_tokens = [query_normalized]
    return [token for token in expand_query_tokens(filtered_tokens) if len(token) >= 3 or token in SHORT_TECH_TOKENS]


def detect_domain(words):
    domain_scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    for word in words:
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if word in keywords:
                domain_scores[domain] += 1

    best_domain = None
    best_score = 0
    for domain, score in domain_scores.items():
        if score > best_score:
            best_domain = domain
            best_score = score

    confident = best_score >= 2
    return best_domain, best_score, confident


def compute_search_score(query_normalized, query_tokens, query_domain, query_domain_confident, product):
    name_normalized = normalize_text(product.name)
    description_normalized = normalize_text(product.description)
    store_normalized = normalize_text(product.store.name)
    primary_image_name = normalize_text(getattr(getattr(product, 'image', None), 'name', ''))
    gallery_image_names = ' '.join(
        normalize_text(getattr(image.image, 'name', '')) for image in product.images.all()[:3]
    )
    combined_text = (
        f"{name_normalized} {description_normalized} {store_normalized} "
        f"{primary_image_name} {gallery_image_names}"
    ).strip()

    query_compact = query_normalized.replace(' ', '')
    name_compact = name_normalized.replace(' ', '')
    combined_compact = combined_text.replace(' ', '')
    combined_words = get_word_set(combined_text)
    name_words = get_word_set(name_normalized)

    score = 0.0
    token_hits = 0
    name_hits = 0
    best_name_similarity = 0.0
    best_text_similarity = 0.0
    exact_phrase_hit = bool(query_compact and query_compact in combined_compact)
    product_domain, product_domain_score, _ = detect_domain(combined_words)
    domain_match = False
    domain_mismatch = False

    if query_domain and query_domain_confident:
        if product_domain == query_domain and product_domain_score > 0:
            score += 40
            domain_match = True
        elif product_domain and product_domain != query_domain:
            score -= 45
            domain_mismatch = True
        else:
            score -= 8

    if exact_phrase_hit:
        score += 80

    if query_compact and query_compact in name_compact:
        score += 180
        token_hits += 1
        name_hits += 1
    elif query_normalized and query_normalized in name_normalized:
        score += 140
        token_hits += 1
        name_hits += 1

    for token in query_tokens:
        if token in name_words:
            score += 45
            token_hits += 1
            name_hits += 1
            continue

        if token in combined_words:
            score += 16
            token_hits += 1

        name_similarity = best_token_similarity(token, name_words)
        text_similarity = best_token_similarity(token, combined_words)
        best_name_similarity = max(best_name_similarity, name_similarity)
        best_text_similarity = max(best_text_similarity, text_similarity)

        if name_similarity >= 0.86:
            score += 30
            token_hits += 1
            name_hits += 1
        elif name_similarity >= 0.74:
            score += 18
            token_hits += 1
            name_hits += 1
        elif text_similarity >= 0.88:
            score += 14
            token_hits += 1

    name_global_similarity = levenshtein_similarity(query_compact, name_compact)
    text_global_similarity = levenshtein_similarity(query_compact, combined_compact)
    best_name_similarity = max(best_name_similarity, name_global_similarity)
    best_text_similarity = max(best_text_similarity, text_global_similarity)

    score += (name_global_similarity * 70) + (text_global_similarity * 20)

    if best_name_similarity >= 0.88:
        score += 25
    elif best_name_similarity >= 0.76:
        score += 12

    if best_text_similarity >= 0.90:
        score += 10

    if not token_hits and best_text_similarity < 0.78:
        score -= 25

    if len(query_tokens) == 1 and not name_hits and best_name_similarity < 0.72 and not exact_phrase_hit:
        score -= 20

    coverage = token_hits / max(len(query_tokens), 1)
    score += coverage * 30

    return (
        score,
        token_hits,
        name_hits,
        best_name_similarity,
        best_text_similarity,
        exact_phrase_hit,
        domain_match,
        domain_mismatch,
    )

def home(request):
    query = request.GET.get('q', '').strip()
    all_products = list(
        Product.objects.select_related('store').prefetch_related('images').all()
    )
    products = all_products

    if query:
        query_normalized = normalize_text(query)
        query_tokens = build_search_tokens(query_normalized)

        ai_intent = detect_search_intent_ai(query_normalized, query_tokens)
        query_tokens = ai_intent['expanded_tokens']

        query_words = set(query_tokens) | get_word_set(query_normalized)
        query_domain, _, query_domain_confident = detect_domain(query_words)

        if ai_intent['confident']:
            query_domain = INTENT_TO_DOMAIN.get(ai_intent['intent'], query_domain)
            query_domain_confident = True

        scored = []
        for product in all_products:
            (
                score,
                token_hits,
                name_hits,
                name_similarity,
                text_similarity,
                exact_phrase_hit,
                domain_match,
                domain_mismatch,
            ) = compute_search_score(
                query_normalized,
                query_tokens,
                query_domain,
                query_domain_confident,
                product,
            )

            # Similar-product detection gate.
            has_token_match = token_hits > 0
            has_name_match = name_hits > 0
            strong_name_fuzzy = name_similarity >= 0.84
            moderate_name_fuzzy = name_similarity >= 0.74 and has_token_match
            strong_text_fuzzy = text_similarity >= 0.90 and has_token_match
            enough_hits = token_hits >= max(1, min(2, len(query_tokens)))
            acceptable_score = score >= 46
            base_similarity = max(name_similarity, text_similarity)
            similarity_ok = base_similarity >= 0.60
            domain_ok = (
                not query_domain_confident
                or domain_match
                or (not domain_mismatch and base_similarity >= 0.82)
            )

            if (
                domain_ok and (
                    exact_phrase_hit
                    or strong_name_fuzzy
                    or moderate_name_fuzzy
                    or strong_text_fuzzy
                    or (has_token_match and similarity_ok)
                    or (has_name_match and enough_hits and acceptable_score)
                )
            ):
                scored.append((score, product))

        scored.sort(key=lambda item: item[0], reverse=True)
        products = [product for _, product in scored]

    return render(request, 'store/index.html', {
        'products': products,
        'query': query,
    })

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
    size_choices = get_product_size_choices(product)

    if product.stock <= 0:
        messages.error(request, 'This product is out of stock.')
        return redirect('product_detail', pk=pk)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    initial_quantity = int(request.POST.get('quantity', request.GET.get('quantity', 1)))
    if initial_quantity < 1:
        initial_quantity = 1
    if initial_quantity > product.stock:
        initial_quantity = product.stock

    initial_data = {
        'quantity': initial_quantity,
        'size': size_choices[0][0],
        'location': profile.location,
        'address': profile.default_address,
    }

    if request.method == 'POST' and request.POST.get('confirm_order') == '1':
        form = BuyNowForm(request.POST, size_choices=size_choices)
        max_stock = product.stock
        form.fields['quantity'].max_value = max_stock

        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if quantity > max_stock:
                messages.error(request, f'Only {max_stock} item(s) are available in stock.')
                return redirect('buy_product', pk=pk)

            total_price = Decimal(product.discounted_price) * quantity

            Order.objects.create(
                user=request.user,
                product=product,
                quantity=quantity,
                size=form.cleaned_data['size'],
                total_price=total_price,
                address=form.cleaned_data['address'],
                location=form.cleaned_data['location'],
                payment_method=form.cleaned_data['payment_method'],
                payment_status=Order.PAYMENT_STATUS_PENDING,
            )

            product.stock -= quantity
            product.save(update_fields=['stock'])

            profile.location = form.cleaned_data['location']
            profile.default_address = form.cleaned_data['address']
            profile.save(update_fields=['location', 'default_address', 'updated_at'])

            messages.success(request, f'Order placed for {product.name}. Admin can review it in the admin panel.')
            return redirect('home')
    else:
        form = BuyNowForm(initial=initial_data, size_choices=size_choices)
        form.fields['quantity'].max_value = product.stock

    return render(request, 'store/buy_now.html', {
        'product': product,
        'form': form,
        'size_choices': size_choices,
    })




def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})


@login_required
def user_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Location and address updated successfully.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'store/profile.html', {'form': form})



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
def checkout_cart(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = list(cart.items.select_related('product'))

    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('view_cart')

    initial_data = {
        'location': profile.location,
        'address': profile.default_address,
    }

    if request.method == 'POST':
        form = CartCheckoutForm(request.POST)
        if form.is_valid():
            # Validate stock before creating orders.
            for item in cart_items:
                if item.quantity > item.product.stock:
                    messages.error(request, f'Not enough stock for {item.product.name}.')
                    return redirect('view_cart')

            for item in cart_items:
                total_price = Decimal(item.product.discounted_price) * item.quantity
                Order.objects.create(
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    total_price=total_price,
                    address=form.cleaned_data['address'],
                    location=form.cleaned_data['location'],
                    payment_method=form.cleaned_data['payment_method'],
                    payment_status=Order.PAYMENT_STATUS_PENDING,
                )

                item.product.stock -= item.quantity
                item.product.save(update_fields=['stock'])

            cart.items.all().delete()

            profile.location = form.cleaned_data['location']
            profile.default_address = form.cleaned_data['address']
            profile.save(update_fields=['location', 'default_address', 'updated_at'])

            messages.success(request, 'Order requests submitted successfully. Admin can review all details in admin panel.')
            return redirect('home')
    else:
        form = CartCheckoutForm(initial=initial_data)

    total_price = sum(item.get_total_price() for item in cart_items)
    return render(request, 'store/checkout_cart.html', {
        'form': form,
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

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/my_orders.html', {'orders': orders})

@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Check if the user is the owner or an admin
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('home')

    if order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=['status'])
        
        # Restore stock
        order.product.stock += order.quantity
        order.product.save(update_fields=['stock'])
        
        messages.success(request, f'Order #{order.id} for {order.product.name} has been successfully cancelled.')
    else:
        messages.error(request, f'Order #{order.id} cannot be cancelled because it is already {order.get_status_display().lower()}.')
        
    if request.user.is_staff:
        # If admin is cancelling from storefront, redirect appropriately
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    return redirect('my_orders')
