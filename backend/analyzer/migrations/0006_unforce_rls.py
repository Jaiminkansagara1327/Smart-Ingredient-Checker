"""
Migration: 0006_unforce_rls

WHY THIS EXISTS
---------------
Previous migration (0005) enabled FORCE ROW LEVEL SECURITY.
This caused the Django backend connection to be subject to RLS even though 
it is the table owner. Since no policies were defined, Django effectively 
saw empty tables, breaking login and registration.

This migration removes the FORCE flag. Standard ENABLE RLS remains active,
which continues to block Supabase's anonymous PostgREST API (solving the 
security warnings) while allowing Django's direct connection to work.
"""
from django.db import connection
from django.db import migrations

_TABLES = [
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "django_session",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "auth_permission",
    "auth_group",
    "auth_group_permissions",
    "analyzer_contactmessage",
    "analyzer_product",
    "analyzer_userprofile",
    "analyzer_searchevent",
    "analyzer_productfavorite",
    "analyzer_analysisrecord",
]

def unforce_rls(apps, schema_editor):
    if connection.vendor == "sqlite":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            # Check table exists
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);",
                [table]
            )
            (exists,) = cursor.fetchone()
            if exists:
                # Remove FORCE but keep ENABLE
                cursor.execute(f'ALTER TABLE public."{table}" NO FORCE ROW LEVEL SECURITY;')
                print(f"  [RLS] Unforced RLS on public.{table}")

def reforce_rls(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            cursor.execute(f'ALTER TABLE public."{table}" FORCE ROW LEVEL SECURITY;')

class Migration(migrations.Migration):
    dependencies = [
        ("analyzer", "0005_enable_rls_on_all_tables"),
    ]

    operations = [
        migrations.RunPython(unforce_rls, reverse_code=reforce_rls),
    ]
