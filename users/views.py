from django.shortcuts import redirect
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer
import threading
import requests
import os


User = get_user_model()


def send_verification_email(to_email, verify_url):
    def _send():
        try:
            requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": os.getenv("GMAIL_USER")},
                    "subject": "Verify your ShopApp account",
                    "content": [{"type": "text/plain", "value": f"Click the link below to verify your account:\n\n{verify_url}"}],
                },
                timeout=10,
            )
        except Exception as e:
            print(f"Email send failed: {e}")

    threading.Thread(target=_send, daemon=True).start()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = str(user.verification_token)
        verify_url = request.build_absolute_uri(f"/api/users/verify-email/?token={token}")
        send_verification_email(user.email, verify_url)

        return Response(
            {"message": "Registration successful. Please check your email to verify your account."},
            status=201
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get("token")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        try:
            user = User.objects.get(verification_token=token)
            user.is_verified = True
            user.save()
            return redirect(frontend_url)
        except User.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=400)


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({"message": "Account already verified."}, status=200)

            token = str(user.verification_token)
            verify_url = request.build_absolute_uri(f"/api/users/verify-email/?token={token}")
            send_verification_email(user.email, verify_url)
            return Response({"message": "Verification email sent."}, status=200)
        except User.DoesNotExist:
            return Response({"error": "No account found with that email."}, status=404)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"Logout": "Logout is succesfull"}, status=200)
        except Exception:
            return Response({"error": "invalid token"}, status=400)
