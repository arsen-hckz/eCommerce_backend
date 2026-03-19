from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid



#changing the base user manager so that we can use email as a usename.
class UserManager(BaseUserManager):
    use_in_migrations = True
    def create_user(self,email,username,password = None,**extra_fields):
        if not email:
            raise ValueError("email is required")
       
        email = self.normalize_email(email)
        user =self.model(email = email,username = username,**extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    def create_superuser(self,email,username,password = None,**extra_fields):
        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)
        extra_fields.setdefault("is_admin",True)
        if not username:
            username = email.split("@")[0]
        return self.create_user(email,username,password,**extra_fields)
    

class User(AbstractUser):
    email = models.EmailField(unique= True)
    phone = models.CharField(max_length=15, blank= True)
    address = models.TextField(max_length=300,blank=True)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.email
