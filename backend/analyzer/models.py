from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class Product(models.Model):
    """
    Own Indian product database — the single source of truth.
    All data here is clean and never overwritten by an external API.
    """

    # ── Core Identifiers ──────────────────────────────────────────────────────
    barcode = models.CharField(
        max_length=50, unique=True, db_index=True,
        help_text="EAN / UPC barcode"
    )
    name = models.CharField(max_length=512)
    brand = models.CharField(max_length=255, blank=True, default="")
    image_url = models.URLField(max_length=2000, blank=True, default="", help_text="Thumbnail/Small image")
    image_url_full = models.URLField(max_length=2000, blank=True, default="", help_text="High-resolution image")

    # ── Ingredient & Category Data ────────────────────────────────────────────
    ingredients_text = models.TextField(
        blank=True, default="",
        help_text="Full English ingredient list"
    )
    categories = models.TextField(
        blank=True, default="",
        help_text="Comma-separated categories, e.g. 'Noodles, Instant Food'"
    )

    # ── Nutrition (per 100 g) ─────────────────────────────────────────────────
    # Stored as JSON: [{"label": "Energy", "value": 375, "unit": "kcal"}, ...]
    nutriments = models.JSONField(
        null=True, blank=True,
        help_text="Nutrition rows — list of {label, value, unit} dicts"
    )
    nutriments_raw = models.JSONField(
        null=True, blank=True,
        help_text="Raw nutriments dict from OpenFoodFacts for re-processing"
    )

    # ── Grading ───────────────────────────────────────────────────────────────
    nova_group = models.IntegerField(
        null=True, blank=True,
        help_text="NOVA food processing group (1–4)"
    )
    nutriscore_grade = models.CharField(
        max_length=1, blank=True, default="",
        help_text="Nutri-Score grade (a/b/c/d/e)"
    )

    # ── Packaging / Serving ───────────────────────────────────────────────────
    serving_size = models.CharField(max_length=100, blank=True, default="")
    quantity = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Package size, e.g. '200g'"
    )

    # ── Origin ────────────────────────────────────────────────────────────────
    country = models.CharField(
        max_length=100, blank=True, default="",
        help_text="e.g. India, USA"
    )
    is_indian = models.BooleanField(
        default=True,
        help_text="True for Indian brands — shown first in results"
    )

    # ── Quality / Trust ───────────────────────────────────────────────────────
    is_verified = models.BooleanField(
        default=False,
        help_text="Manually confirmed — data is 100% correct"
    )
    source = models.CharField(
        max_length=50, default="OFF",
        help_text="Data origin: OFF (OpenFoodFacts import), Manual"
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_verified", "-is_indian", "name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["is_indian", "is_verified"]),
        ]

    def __str__(self):
        brand = f" — {self.brand}" if self.brand else ""
        return f"{self.name}{brand} [{self.barcode}]"

    def has_ingredients(self):
        return bool(self.ingredients_text and len(self.ingredients_text) > 10)

    def has_nutrition(self):
        return bool(self.nutriments)


class UserProfile(models.Model):
    """
    Stores user-level SaaS preferences and profile data.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True, default="")

    # Simple dietary/preferences toggles (can be expanded later).
    veg_only = models.BooleanField(default=False)
    health_goal = models.CharField(max_length=50, blank=True, default="")

    # Notifications
    notify_email = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or f"Profile of {self.user.email}"


class ProductFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorited_by")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        indexes = [
            models.Index(fields=["user", "product"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.product.barcode}"


class AnalysisRecord(models.Model):
    """
    Stores a saved analysis (history) for a user.

    Note: `user` is nullable to support future anonymous history if you
    choose, but authenticated users will be the primary path.
    """

    INPUT_TEXT = "text"
    INPUT_BARCODE = "barcode"
    INPUT_METHOD_CHOICES = [
        (INPUT_TEXT, "text"),
        (INPUT_BARCODE, "barcode"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="analysis_records",
        null=True,
        blank=True,
    )

    input_method = models.CharField(max_length=20, choices=INPUT_METHOD_CHOICES, default=INPUT_TEXT)

    # Avoid storing huge raw ingredient strings; keep a preview for debugging/history.
    input_text_preview = models.CharField(max_length=400, blank=True, default="")

    # Optional product snapshot fields
    product_name = models.CharField(max_length=512, blank=True, default="")
    product_brand = models.CharField(max_length=255, blank=True, default="")
    product_json = models.JSONField(null=True, blank=True)

    # Scoring/meta
    user_goal = models.CharField(max_length=50, blank=True, default="Regular")
    food_type = models.CharField(max_length=20, blank=True, default="Solid")
    confidence = models.FloatField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    nova_group = models.IntegerField(null=True, blank=True)
    nutriscore_grade = models.CharField(max_length=10, blank=True, default="")

    analysis_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        who = self.user.email if self.user_id else "anonymous"
        return f"AnalysisRecord({who}, {self.input_method}, {self.created_at:%Y-%m-%d})"


class SearchEvent(models.Model):
    """
    Captures search requests for observability/analytics.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="search_events",
        null=True,
        blank=True,
    )

    query = models.CharField(max_length=200)
    local_only = models.BooleanField(default=False)

    ip_address = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=512, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        who = self.user.email if self.user_id else "anonymous"
        return f"SearchEvent({who}, {self.query[:20]})"
