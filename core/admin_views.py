from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
         return request.user and request.user.is_authenticated and (request.user.is_admin or request.user.is_superuser)


class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(
            payment_status="paid"
        ).aggregate(total=Sum("total_price"))["total"] or 0
        total_users = User.objects.count()
        total_products = Product.objects.filter(is_active=True).count()
        pending_orders = Order.objects.filter(status="pending").count()

        top_products = OrderItem.objects.values(
            "product__id", "product__name"
        ).annotate(
            total_sold=Sum("quantity")
        ).order_by("-total_sold")[:5]

        recent_orders = Order.objects.select_related("user").order_by("-created_at")[:5]
        recent_orders_data = [
            {
                "id": order.id,
                "user": order.user.email,
                "total_price": order.total_price,
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at,
            }
            for order in recent_orders
        ]

        return Response({
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_users": total_users,
            "total_products": total_products,
            "pending_orders": pending_orders,
            "top_products": list(top_products),
            "recent_orders": recent_orders_data,
        })


class AdminOrderListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        orders = Order.objects.select_related("user").order_by("-created_at")
        data = [
            {
                "id": order.id,
                "user": order.user.email,
                "total_price": order.total_price,
                "status": order.status,
                "payment_status": order.payment_status,
                "shipping_address": order.shipping_address,
                "created_at": order.created_at,
            }
            for order in orders
        ]
        return Response(data)


class AdminOrderUpdateView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        status = request.data.get("status")
        if status not in ["pending", "processing", "shipped", "delivered", "cancelled"]:
            return Response({"error": "Invalid status"}, status=400)

        order.status = status
        order.save()
        return Response({"message": "Order updated", "status": order.status})


class AdminUserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        data = [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin,
                "date_joined": user.date_joined,
            }
            for user in users
        ]
        return Response(data)


class AdminProductListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        products = Product.objects.select_related("category").order_by("-created_at")
        data = [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "stock": product.stock,
                "category": product.category.name if product.category else None,
                "is_active": product.is_active,
            }
            for product in products
        ]
        return Response(data)