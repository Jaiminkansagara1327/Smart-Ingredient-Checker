from django.db import models


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
