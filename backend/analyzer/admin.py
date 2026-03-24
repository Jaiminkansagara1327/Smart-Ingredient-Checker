from django.contrib import admin
from .models import ContactMessage, Product


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'brand', 'barcode', 'country',
        'nova_group', 'nutriscore_grade',
        'is_indian', 'is_verified', 'source', 'updated_at',
    )
    list_filter = (
        'is_verified', 'is_indian', 'nova_group',
        'nutriscore_grade', 'source', 'country',
    )
    search_fields = ('name', 'brand', 'barcode', 'ingredients_text')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_verified', 'is_indian')
    ordering = ('-is_verified', '-is_indian', 'name')

    fieldsets = (
        ('Core Info', {
            'fields': ('barcode', 'name', 'brand', 'image_url', 'quantity', 'serving_size'),
        }),
        ('Ingredient & Category Data', {
            'fields': ('ingredients_text', 'categories'),
        }),
        ('Grading', {
            'fields': ('nova_group', 'nutriscore_grade'),
        }),
        ('Nutrition', {
            'classes': ('collapse',),
            'fields': ('nutriments', 'nutriments_raw'),
        }),
        ('Origin & Trust', {
            'fields': ('country', 'is_indian', 'is_verified', 'source'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
