from django.urls import path
from .views import (
    CartView, AddToCartView, RemoveFromCartView,
    UpdateCartItemView, OrderListView, CreateOrderView, OrderDetailView
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="cart-add"),
    path("cart/remove/<int:item_id>/", RemoveFromCartView.as_view(), name="cart-remove"),
    path("cart/update/<int:item_id>/", UpdateCartItemView.as_view(), name="cart-update"),
    path("", OrderListView.as_view(), name="order-list"),
    path("create/", CreateOrderView.as_view(), name="order-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
]