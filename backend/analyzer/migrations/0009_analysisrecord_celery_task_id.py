from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds celery_task_id to AnalysisRecord so that analyze_ingredients_task
    can use get_or_create() for idempotent writes on Celery retries.

    The unique constraint on celery_task_id is the database-level guard:
    even if two worker processes race on a retry, only one INSERT can win;
    the other will hit the constraint and get_or_create() returns the
    existing row instead of raising an unhandled IntegrityError.
    """

    dependencies = [
        ("analyzer", "0008_enable_rls_token_blacklist"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysisrecord",
            name="celery_task_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Celery task UUID — used for retry-safe deduplication.",
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
    ]