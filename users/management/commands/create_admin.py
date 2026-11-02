import os

from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Create a superuser from ADMIN_EMAIL, ADMIN_USERNAME and ADMIN_PASSWORD; does nothing if they are unset."

    def handle(self, *args, **kwargs):
        email = os.getenv("ADMIN_EMAIL")
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD")
        if not email or not password:
            self.stdout.write("ADMIN_EMAIL / ADMIN_PASSWORD not set, skipping")
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write("Superuser already exists")
            return

        User.objects.create_superuser(email=email, username=username, password=password)
        self.stdout.write("Superuser created")
