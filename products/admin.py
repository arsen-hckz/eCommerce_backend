from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib import messages
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "is_active", "add_stock_button"]
    list_filter = ["category", "is_active"]
    search_fields = ["name"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:product_id>/add-stock/", self.admin_site.admin_view(self.add_stock_view), name="product-add-stock"),
        ]
        return custom_urls + urls

    def add_stock_button(self, obj):
        url = reverse("admin:product-add-stock", args=[obj.pk])
        return format_html('<a class="button" href="{}">Add Stock</a>', url)
    add_stock_button.short_description = "Stock Action"

    def add_stock_view(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        if request.method == "POST":
            amount = int(request.POST.get("amount", 0))
            if amount > 0:
                product.stock += amount
                product.save()
                messages.success(request, f"Added {amount} units to {product.name}. New stock: {product.stock}.")
            else:
                messages.error(request, "Amount must be greater than 0.")
            return redirect("admin:products_product_changelist")

        from django.template.response import TemplateResponse
        return TemplateResponse(request, "admin/products/add_stock.html", {
            "product": product,
            "opts": self.model._meta,
            "title": f"Add Stock to {product.name}",
        })
