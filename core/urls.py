from django.urls import path
from core import views
from core.views import *  # This imports all views from core, including tag_products_view
from django.conf.urls import include
from .views import cart_info_api, add_product_review

# Remove the line: from userauths import views

app_name = 'core'
urlpatterns = [
    path('', index, name='index'),
    path('products/', product_list_view, name='product_list_view'),
    path('categories/<str:cid>/', category_products_view, name='category_product'),
    path('products/<str:pid>/', product_details_view, name='product_details'), 
    path('tag/<slug:tag_slug>/', tag_products_view, name='tag_products'),  # Now correctly references core.views
    path('search/', search_view, name='search'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout_view, name='checkout'),
    path('order/confirmation/<str:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('cart/apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
]
urlpatterns += [
    path('cart/api/info/', cart_info_api, name='cart_info_api'),
    path('products/<str:pid>/add-review/', add_product_review, name='add_product_review'),
]