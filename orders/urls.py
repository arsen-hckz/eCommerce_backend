from django.urls import path
from .views import (
    CartView, AddToCartView, RemoveFromCartView,
    UpdateCartItemView, OrderListView, CreateOrderView, UpdateOrderView,
    OrderDetailView, CreateCheckOutSessionView, stripe_webhook, VerifyPaymentView
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="cart-add"),
    path("cart/remove/<int:item_id>/", RemoveFromCartView.as_view(), name="cart-remove"),
    path("cart/update/<int:item_id>/", UpdateCartItemView.as_view(), name="cart-update"),
    path("", OrderListView.as_view(), name="order-list"),
    path("create/", CreateOrderView.as_view(), name="order-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:order_id>/checkout/", CreateCheckOutSessionView.as_view()),
    path("webhook/", stripe_webhook, name="stripe-webhook"),
    path("<int:pk>/update-address/", UpdateOrderView.as_view(), name="order-update-address"),
    path("<int:order_id>/verify-payment/", VerifyPaymentView.as_view(), name="order-verify-payment"),
]