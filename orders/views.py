from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, CreateOrderSerializer
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import json , stripe




class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart,context = {"request":request})
        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        try:
            from products.models import Product
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        if product.stock < quantity:
            return Response({"error": "Not enough stock"}, status=400)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response(CartSerializer(cart, context={"request": request}).data)


class RemoveFromCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            return Response({"message": "Item removed"}, status=200)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)


class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            quantity = int(request.data.get("quantity", 1))
            if quantity <= 0:
                cart_item.delete()
                return Response({"message": "Item removed"})
            cart_item.quantity = quantity
            cart_item.save()
            return Response(CartItemSerializer(cart_item).data)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print("User:", request.user)
        print("User ID:", request.user.id)
        cart = Cart.objects.filter(user=request.user).first()
        print("Cart:", cart)
        print("Cart items:", cart.items.all() if cart else "No cart")
    
        if not cart or not cart.items.exists():
          return Response({"error": "Your cart is empty"}, status=400)

        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # create the order
        order = Order.objects.create(
            user=request.user,
            total_price=cart.total,
            shipping_address=serializer.validated_data.get("shipping_address",""))
        

        # create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            # reduce stock
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()

        # clear the cart after order is placed
        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=201)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    


class CreateCheckOutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request,order_id):
        try:
            order = Order.objects.get(id=order_id, user = request.user)
        except Order.DoesNotExist:
            return Response({"message":"order doesnt exist"}, status=404)
        if order.payment_status == "paid":
            return Response({"message":"order is already paid"})
        
        line_items = []
        for item in order.items.all():
            line_items.append(
                {"price_data":{
                    "currency":"usd",
                    "product_data":{
                        "name":item.product.name,
                    },
                    "unit_amount":int(item.price * 100)
                },
                "quantity":item.quantity,
                }
            )

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=f"{settings.FRONTEND_URL}/orders/{order.id}?payment=success",
                cancel_url=f"{settings.FRONTEND_URL}/orders/{order.id}?payment=cancelled",
                metadata={"order_id": str(order.id)}
            )
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=400)

        order.stripe_session_id = session.id
        order.save()
        return Response({"checkout_url":session.url})
        


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print("ValueError:", e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print("SignatureVerificationError:", e)
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session["metadata"]["order_id"]
        try:
            order = Order.objects.get(id=order_id)
            order.payment_status = "paid"
            order.status = "processing"
            order.save()
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)

class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.payment_status == "paid":
            return Response(OrderSerializer(order).data)

        if not order.stripe_session_id:
            return Response({"error": "No session found"}, status=400)

        try:
            session = stripe.checkout.Session.retrieve(order.stripe_session_id)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=400)

        if session.payment_status == "paid":
            order.payment_status = "paid"
            order.status = "processing"
            order.save()

        return Response(OrderSerializer(order).data)


class UpdateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        shipping_address = request.data.get("shipping_address")
        if shipping_address:
            order.shipping_address = shipping_address
            order.save()
        return Response(OrderSerializer(order).data)