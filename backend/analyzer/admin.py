from django.contrib import admin
from .models import (
    ContactMessage,
    Product,
    UserProfile,
    ProductFavorite,
    AnalysisRecord,
    SearchEvent,
)


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'health_goal', 'veg_only', 'notify_email', 'updated_at')
    list_filter = ('veg_only', 'notify_email', 'health_goal')
    search_fields = ('user__email', 'user__username', 'display_name')


@admin.register(ProductFavorite)
class ProductFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name', 'product__barcode')
    readonly_fields = ('created_at',)


@admin.register(AnalysisRecord)
class AnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'input_method', 'product_name', 'score', 'nova_group', 'created_at')
    list_filter = ('input_method', 'nova_group', 'created_at')
    search_fields = ('user__email', 'product_name', 'input_text_preview')
    readonly_fields = ('created_at',)


@admin.register(SearchEvent)
class SearchEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'query', 'local_only', 'ip_address', 'created_at')
    list_filter = ('local_only', 'created_at')
    search_fields = ('query', 'user__email', 'ip_address')
    readonly_fields = ('created_at',)
