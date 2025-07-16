from django.shortcuts import render, get_object_or_404 ,redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db import models
from core.models import *
from taggit.models import Tag
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import logging
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import SiteSetting, Coupon
from django.utils import timezone
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
# __________________Index View____________________
def index(request):
    products = Product.objects.filter(is_new=True, status='published').order_by('-created_at')[:8]
    categories = Category.objects.all().annotate(
        product_count=Count('category_products', filter=Q(category_products__status='published'))
    )
    brand = BrandInfo.objects.first()

    clothing = Category.objects.get(title="Clothing")
    accessories = Category.objects.get(title="Accessories")
    shoes = Category.objects.get(title="Shoes")
    
    context = {
        'products': products,
        'categories': categories,
        'clothing': clothing,
        'accessories': accessories,
        'shoes': shoes,
        'brand': brand,
        'title': 'Homepage',
    }
    return render(request, 'core/index.html', context)

# __________________Product List View____________________
def product_list_view(request):
    brand = BrandInfo.objects.first()
    category_id = request.GET.get('category')
    vendor_id = request.GET.get('vendor')
    tag_slug = request.GET.get('tag')
    price_range = request.GET.get('price')  # ✅ فلتر السعر
    product_type = request.GET.get('type')

    products = Product.objects.filter(status='published') \
        .select_related('vendor', 'category') \
        .prefetch_related('tags')

    if category_id:
        products = products.filter(category__id=category_id)

    if vendor_id:
        products = products.filter(vendor__id=vendor_id)

    if tag_slug:
        products = products.filter(tags__slug=tag_slug)

    if price_range:
        try:
            min_price, max_price = price_range.split('-')
            if min_price:
                products = products.filter(price__gte=float(min_price))
            if max_price:
                products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass  # تجاهل القيمة لو مش صحيحة

    if product_type == 'active':
        products = products.filter(is_active=True)
    elif product_type == 'published':
        products = products.filter(is_published=True)
    elif product_type == 'digital':
        products = products.filter(digital=True)
    elif product_type == 'featured':
        products = products.filter(is_featured=True)
    elif product_type == 'new':
        products = products.filter(is_new=True)
    elif product_type == 'best_seller':
        products = products.filter(is_best_seller=True)
    elif product_type == 'discounted':
        products = products.filter(is_discounted=True)
    elif product_type == 'on_sale':
        products = products.filter(is_on_sale=True)
    elif product_type == 'returnable':
        products = products.filter(is_returnable=True)
    elif product_type == 'refundable':
        products = products.filter(is_refundable=True)
    elif product_type == 'verified':
        products = products.filter(is_verified=True)
    elif product_type == 'archived':
        products = products.filter(is_archived=True)

    # إعداد قائمة الأنواع المتوفرة فعليًا فقط
    type_options = []
    if Product.objects.filter(is_on_sale=True).exists():
        type_options.append(('on_sale', 'On Sale'))
    if Product.objects.filter(is_new=True).exists():
        type_options.append(('new', 'New Arrival'))
    if Product.objects.filter(is_best_seller=True).exists():
        type_options.append(('best_seller', 'Best Seller'))
    if Product.objects.filter(is_featured=True).exists():
        type_options.append(('featured', 'Featured'))
    if Product.objects.filter(is_verified=True).exists():
        type_options.append(('verified', 'Verified'))
    if Product.objects.filter(is_active=True).exists():
        type_options.append(('active', 'Active'))
    if Product.objects.filter(is_published=True).exists():
        type_options.append(('published', 'Published'))
    if Product.objects.filter(digital=True).exists():
        type_options.append(('digital', 'Digital Product'))
    if Product.objects.filter(is_discounted=True).exists():
        type_options.append(('discounted', 'Discounted'))
    if Product.objects.filter(is_returnable=True).exists():
        type_options.append(('returnable', 'Returnable'))
    if Product.objects.filter(is_refundable=True).exists():
        type_options.append(('refundable', 'Refundable'))
    if Product.objects.filter(is_archived=True).exists():
        type_options.append(('archived', 'Archived'))

    products = products.order_by('-created_at')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'products': page_obj,
        'categories': Category.objects.annotate(
            product_count=Count('category_products', filter=Q(category_products__status='published'))
        ),
        'vendors': Vendor.objects.all(),
        'tags': Tag.objects.all(),
        'title': 'All Collections',
        'brand': brand,
        'category_id': category_id,
        'wishlist_product_ids': wishlist_product_ids,
        'type_options': type_options,
    }
    return render(request, 'core/products.html', context)





# __________________Category Products View____________________

def category_products_view(request, cid):
    brand = BrandInfo.objects.first()
    category = get_object_or_404(Category, cid=cid)

    products_qs = Product.objects.filter(
        category=category,
        status='published'
    ).select_related('vendor', 'category') \
     .prefetch_related('tags') \
     .order_by('-created_at')  # ترتيب أحدث أولاً

    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'products': page_obj,
        'vendors': Vendor.objects.all(),
        'tags': Tag.objects.all(),
        'paginator': paginator,
        'title': 'Category: ' + category.title,  # إضافة عنوان الصفحة
        'brand': brand,  # إضافة معلومات العلامة التجارية
    }
    return render(request, 'core/category_products.html', context)




# _________________________Product Details View____________________
def product_details_view(request, pid):
    brand = BrandInfo.objects.first()

    product = get_object_or_404(
        Product.objects.select_related('vendor', 'category')
                       .prefetch_related('tags', 'additional_images'),
        pid=pid,
        status='published'
    )

    category_id = request.GET.get('category')
    categories = Category.objects.all()

    # تصفية المنتجات (مثلاً لعرضها في sidebar أو قائمة فرعية)
    if category_id:
        filtered_products = Product.objects.filter(status='published', category_id=category_id)
    else:
        filtered_products = Product.objects.filter(status='published')

    related_products = Product.objects.filter(
        category=product.category,
        status='published'
    ).exclude(pid=pid)[:4]

    can_review = False
    if request.user.is_authenticated:
        can_review = not product.reviews.filter(user=request.user).exists()
    context = {
        'product': product,
        'additional_images': product.additional_images.all(),
        'related_products': related_products,
        'vendors': Vendor.objects.all(),
        'tags': Tag.objects.all(),
        'title': product.title,
        'brand': brand,
        'categories': categories,
        'category_id': category_id,
        'filtered_products': filtered_products,  # ← يمكنك استخدامه في القالب إذا كنت تريد عرضها
        'can_review': can_review,
    }

    return render(request, 'core/product_details.html', context)




def tag_products_view(request, tag_slug):
    brand = BrandInfo.objects.first()
    tag = get_object_or_404(Tag, slug=tag_slug)
    products = Product.objects.filter(tags__slug=tag_slug, status='published') \
                              .select_related('vendor', 'category') \
                              .order_by('-created_at')

    context = {
        'tag': tag,
        'products': products,
        'vendors': Vendor.objects.all(),
        'categories': Category.objects.all(),
        'title': f'Tag: {tag.name}',  # إضافة عنوان الصفحة
        'brand': brand,  # إضافة معلومات العلامة التجارية
    }
    return render(request, 'core/tag_products.html', context)




def search_view(request):
    brand = BrandInfo.objects.first()
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(status='published')

    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    products = products.select_related('vendor', 'category').order_by('-created_at')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'query': query,
        'result_count': products.count(),
        'vendors': Vendor.objects.all(),
        'categories': Category.objects.all(),
        'title': f'Search Results for "{query}"',  # إضافة عنوان الصفحة
        'brand': brand,  # إضافة معلومات العلامة التجارية
    }
    return render(request, 'core/search_results.html', context)

 

@login_required
def cart_view(request):
    brand = BrandInfo.objects.first()
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        customer = Customer.objects.create(user=request.user)

    cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
    cart_items = cart.items.all()

    # جلب سعر الشحن من قاعدة البيانات
    shipping_setting = SiteSetting.objects.first()
    shipping_price = shipping_setting.shipping_price if shipping_setting else 0

    # حساب الخصم إذا وُجد كوبون
    coupon_code = request.session.get('applied_coupon')
    coupon = None
    discount = 0
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
            if coupon.is_valid(cart.total_price):
                discount = coupon.get_discount_amount(cart.total_price)
            else:
                # الكوبون غير صالح، احذفه من السيشن
                del request.session['applied_coupon']
                coupon = None
        except Coupon.DoesNotExist:
            coupon = None
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

    subtotal = cart.total_price
    total = subtotal - discount + shipping_price

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'shipping_price': shipping_price,
        'coupon': coupon,
        'discount': discount,
        'subtotal': subtotal,
        'total': total,
        'brand': brand,
    }
    return render(request, 'core/shopping_cart.html', context)


@login_required
@require_POST
def add_to_cart(request, product_id):
    try:
        # تحقق من وجود المنتج
        product = Product.objects.get(pid=product_id)
        
        # تحقق من الكمية
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'الكمية يجب أن تكون على الأقل 1'
            }, status=400)
            
        # تحقق من المخزون
        if product.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'لا يوجد مخزون كافي (المتبقي: {product.stock_quantity})'
            }, status=400)
            
        # إنشاء/جلب السلة
        customer, created = Customer.objects.get_or_create(user=request.user)
        cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
        
        # استقبال اللون (اسم|كود)
        color_value = request.POST.get('color')
        color_name, color_hex = None, None
        if color_value and '|' in color_value:
            color_name, color_hex = color_value.split('|', 1)
        elif color_value:
            color_hex = color_value

        # إضافة المنتج للسلة
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'price': product.price,
                'user': request.user,
                'color': color_hex,
                'color_hex': color_hex,
                'color_name': color_name,
                'size': request.POST.get('size'),
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            # تحديث اللون والمقاس إذا تم تغييره
            if color_hex:
                cart_item.color = color_hex
                cart_item.color_hex = color_hex
            if color_name:
                cart_item.color_name = color_name
            cart_item.size = request.POST.get('size') or cart_item.size
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'تمت إضافة {product.title} إلى السلة',
            'item_count': cart.items.count()
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'المنتج غير موجود'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def update_cart_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be at least 1'
            }, status=400)
            
        # Check stock availability
        if quantity > cart_item.product.stock_quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {cart_item.product.stock_quantity} items available'
            }, status=400)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        cart = cart_item.cart
        # جلب سعر الشحن من قاعدة البيانات
        shipping_setting = SiteSetting.objects.first()
        shipping_price = float(shipping_setting.shipping_price) if shipping_setting else 0
        # حساب الخصم إذا وُجد كوبون
        coupon_code = request.session.get('applied_coupon')
        coupon = None
        discount = 0
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if coupon.is_valid(cart.total_price):
                    discount = float(coupon.get_discount_amount(cart.total_price))
                else:
                    del request.session['applied_coupon']
                    coupon = None
            except Coupon.DoesNotExist:
                coupon = None
                if 'applied_coupon' in request.session:
                    del request.session['applied_coupon']
        subtotal = float(cart.total_price)
        total = subtotal - discount + shipping_price
        return JsonResponse({
            'success': True,
            'item_total': float(cart_item.total_price),
            'cart_total': subtotal,
            'item_count': cart.items.count(),
            'subtotal': subtotal,
            'discount': discount,
            'shipping_price': shipping_price,
            'total': total
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer__user=request.user)
        cart = cart_item.cart
        product_name = cart_item.product.title
        cart_item.delete()
        # جلب سعر الشحن من قاعدة البيانات
        shipping_setting = SiteSetting.objects.first()
        shipping_price = float(shipping_setting.shipping_price) if shipping_setting else 0
        # حساب الخصم إذا وُجد كوبون
        coupon_code = request.session.get('applied_coupon')
        coupon = None
        discount = 0
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if coupon.is_valid(cart.total_price):
                    discount = float(coupon.get_discount_amount(cart.total_price))
                else:
                    del request.session['applied_coupon']
                    coupon = None
            except Coupon.DoesNotExist:
                coupon = None
                if 'applied_coupon' in request.session:
                    del request.session['applied_coupon']
        subtotal = float(cart.total_price)
        total = subtotal - discount + shipping_price
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_total': subtotal,
            'item_count': cart.items.count(),
            'subtotal': subtotal,
            'discount': discount,
            'shipping_price': shipping_price,
            'total': total
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    



logger = logging.getLogger(__name__)

@login_required
@csrf_protect
@transaction.atomic
def checkout_view(request):
    try:
        customer = request.user.customer
    except Exception:
        messages.error(request, "Customer profile not found.")
        return redirect('core:cart_view')

    cart = get_object_or_404(Cart, customer=customer, completed=False)
    cart_items = cart.items.all()

    # جلب سعر الشحن من قاعدة البيانات
    shipping_setting = SiteSetting.objects.first()
    shipping_cost = shipping_setting.shipping_price if shipping_setting else Decimal('0.00')

    # حساب الخصم إذا وُجد كوبون
    coupon_code = request.session.get('applied_coupon')
    coupon = None
    discount = Decimal('0.00')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
            if coupon.is_valid(cart.total_price):
                discount = coupon.get_discount_amount(cart.total_price)
            else:
                del request.session['applied_coupon']
                coupon = None
        except Coupon.DoesNotExist:
            coupon = None
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

    subtotal = cart.total_price
    tax_rate = Decimal('0.05')
    tax_amount = subtotal * tax_rate
    total = subtotal - discount + tax_amount + shipping_cost

    if request.method == 'POST':
        try:
            required_fields = ['address', 'city', 'state', 'postcode', 'country', 'payment_method']
            for field in required_fields:
                if not request.POST.get(field):
                    raise ValidationError(f"Missing required field: {field}")

            address = Address.objects.create(
                user=request.user,
                address_type='shipping',
                address_line1=request.POST.get('address'),
                address_line2=request.POST.get('address2', ''),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                postal_code=request.POST.get('postcode'),
                country=request.POST.get('country'),
                is_default=False,
                phone=request.POST.get('phone')
            )

            order = CartOrder.objects.create(
                user=request.user,
                shipping_address=address,
                payment_method=request.POST.get('payment_method'),
                sub_total=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_cost,
                total=total,
                paid_status=True if request.POST.get('payment_method') == 'cash_on_delivery' else False,
                status='processing',
                phone_number=request.POST.get('phone')
            )

            for item in cart_items:
                CartItem.objects.create(
                    order=order,
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.price,
                    color=item.color,
                    color_hex=item.color_hex,
                    color_name=item.color_name,
                    size=item.size
                )
                # تحديث المخزون
                product = item.product
                product.stock_quantity -= item.quantity
                product.items_sold += item.quantity
                product.save()

            cart.completed = True
            cart.order = order
            cart.save()

            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

            # إرسال الإيميل هنا فقط بعد نجاح الطلب
            customer_name = request.user.get_full_name() or request.user.username
            customer_email = request.user.email
            customer_phone = request.POST.get('phone')
            shipping_address = f"{request.POST.get('address')}, {request.POST.get('city')}, {request.POST.get('state')}, {request.POST.get('country')}, {request.POST.get('postcode')}"

            product_lines = ""
            for item in cart_items:
                product_lines += (
                    f"- {item.product.title} | Quantity: {item.quantity} | "
                    f"Color: {item.color_name or '-'} | Size: {item.size or '-'} | "
                    f"Unit Price: {item.price} | Total: {item.price * item.quantity}\n"
                )

            coupon_code = request.session.get('applied_coupon')
            discount_line = ""
            if coupon_code and coupon:
                discount_line = f"\nDiscount Code Used: {coupon_code} | Value: {discount}\n"
            else:
                discount_line = "\nNo discount code used.\n"

            total_line = f"\nOrder Total: {total}\n"

            fraud_warning = (
                "\n[Notice] Please verify the customer's phone and address before processing the order to prevent fraud."
            )

            order_details = f"""
New Order Received!

Customer Name: {customer_name}
Customer Email: {customer_email}
Customer Phone: {customer_phone}

Shipping Address:
{shipping_address}

Products:
{product_lines}
{discount_line}
{total_line}
{fraud_warning}
"""

            send_mail(
                subject=f"New Order from {customer_name}",
                message=order_details,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['mostafasaberfareg@gmail.com'],
                fail_silently=False,
            )

            messages.success(request, "Your order has been placed successfully!")
            return redirect('core:order_confirmation', order_id=order.order_id)

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('core:checkout')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('core:checkout')

    # إرسال إيميل إشعار بالطلب الجديد
    customer_name = request.user.get_full_name() or request.user.username
    customer_email = request.user.email
    customer_phone = request.POST.get('phone')
    shipping_address = f"{request.POST.get('address')}, {request.POST.get('city')}, {request.POST.get('state')}, {request.POST.get('country')}, {request.POST.get('postcode')}"

    product_lines = ""
    for item in cart_items:
        product_lines += (
            f"- {item.product.title} | Quantity: {item.quantity} | "
            f"Color: {item.color_name or '-'} | Size: {item.size or '-'} | "
            f"Unit Price: {item.price} | Total: {item.price * item.quantity}\n"
        )

    coupon_code = request.session.get('applied_coupon')
    discount_line = ""
    if coupon_code and coupon:
        discount_line = f"\nDiscount Code Used: {coupon_code} | Value: {discount}\n"
    else:
        discount_line = "\nNo discount code used.\n"

    total_line = f"\nOrder Total: {total}\n"

    fraud_warning = (
        "\n[Notice] Please verify the customer's phone and address before processing the order to prevent fraud."
    )

    order_details = f"""
New Order Received!

Customer Name: {customer_name}
Customer Email: {customer_email}
Customer Phone: {customer_phone}

Shipping Address:
{shipping_address}

Products:
{product_lines}
{discount_line}
{total_line}
{fraud_warning}
"""

    send_mail(
        subject=f"New Order from {customer_name}",
        message=order_details,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['mostafasaberfareg@gmail.com'],
        fail_silently=False,
    )

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'discount': discount,
        'coupon': coupon,
        'total': total,
        'addresses': Address.objects.filter(user=request.user, address_type='shipping'),
        'payment_methods': [
            {'code': 'credit_card', 'name': 'Credit Card'},
            {'code': 'paypal', 'name': 'PayPal'},
            {'code': 'cash_on_delivery', 'name': 'Cash on Delivery'},
        ],
        'brand': BrandInfo.objects.first(),
    }
    return render(request, 'core/checkout.html', context)


@login_required
def order_confirmation_view(request, order_id):
    order = get_object_or_404(CartOrder, order_id=order_id, user=request.user)

    context = {
        'order': order,
    }
    return render(request, 'core/order_confirmation.html', context)

@login_required
@require_POST
def apply_coupon_view(request):
    code = request.POST.get('code', '').strip()
    customer = request.user.customer
    cart = Cart.objects.filter(customer=customer, completed=False).first()
    if not cart:
        return redirect('core:cart_view')
    if not code:
        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']
        return redirect('core:cart_view')
    try:
        coupon = Coupon.objects.get(code__iexact=code)
        if not coupon.is_valid(cart.total_price):
            # كوبون غير صالح
            request.session['coupon_error'] = 'Coupon is not valid or expired.'
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']
        else:
            request.session['applied_coupon'] = code
            if 'coupon_error' in request.session:
                del request.session['coupon_error']
    except Coupon.DoesNotExist:
        request.session['coupon_error'] = 'Coupon does not exist.'
        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']
    return redirect('core:cart_view')

def cart_info_api(request):
    cart_data = {'count': 0, 'total': '0.00'}
    if request.user.is_authenticated:
        from .models import Cart, Customer
        try:
            customer = request.user.customer
            cart = Cart.objects.filter(customer=customer, completed=False).first()
            if cart:
                cart_data['count'] = cart.items.count()
                cart_data['total'] = f'{cart.total_price:.2f}'
        except Exception:
            pass
    return JsonResponse(cart_data)

@require_POST
def add_product_review(request, pid):
    if not request.user.is_authenticated:
        messages.error(request, "يجب تسجيل الدخول لتقييم المنتج.")
        return redirect('core:product_details', pid=pid)
    product = Product.objects.get(pid=pid)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '').strip()
    # منع التكرار
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.error(request, "لقد قمت بتقييم هذا المنتج من قبل.")
        return redirect('core:product_details', pid=pid)
    ProductReview.objects.create(product=product, user=request.user, rating=rating, comment=comment)
    # تحديث متوسط التقييم
    reviews = ProductReview.objects.filter(product=product)
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    product.rating = avg_rating
    product.save()
    messages.success(request, "تم إرسال تقييمك بنجاح!")
    return redirect('core:product_details', pid=pid)

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect(request.META.get('HTTP_REFERER', 'core:product_list_view'))

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect(request.META.get('HTTP_REFERER', 'core:product_list_view'))

@login_required
def wishlist_list(request):
    brand = BrandInfo.objects.first()
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'core/wishlist.html', {'wishlist_items': wishlist_items, 'brand': brand})