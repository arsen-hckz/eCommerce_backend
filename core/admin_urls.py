from django.urls import path
from .admin_views import (
    DashboardStatsView,
    AdminOrderListView,
    AdminOrderUpdateView,
    AdminUserListView,
    AdminProductListView,
)

urlpatterns = [
    path("stats/", DashboardStatsView.as_view(), name="admin-stats"),
    path("orders/", AdminOrderListView.as_view(), name="admin-orders"),
    path("orders/<int:order_id>/", AdminOrderUpdateView.as_view(), name="admin-order-update"),
    path("users/", AdminUserListView.as_view(), name="admin-users"),
    path("products/", AdminProductListView.as_view(), name="admin-products"),
]