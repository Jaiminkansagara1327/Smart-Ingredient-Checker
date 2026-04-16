"""
Migration: 0007_add_postgres_policy

WHY THIS EXISTS
---------------
Ingrexa connects to Supabase via the Transaction Pooler (port 6543).
In Supabase, the pooler ignores the `BYPASSRLS` attribute. This means that
even though Django connects as the 'postgres' user, it is still subject to 
RLS policies because RLS is 'Enabled'.

Since there were NO policies, Django was denied access to all data.
This migration adds a specific policy to every table that allows the 
'postgres' role (your connection user) to perform all operations.

This keeps RLS 'Enabled' (solving Supabase security warnings) but allows
Django to function correctly through the pooler.
"""

from django.db import migrations
import os

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

def add_owner_policies(apps, schema_editor):
    # Use 'postgres' role which is the default owner/superuser for Supabase.
    role_name = 'postgres'

    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            # Check table exists
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);",
                [table]
            )
            (exists,) = cursor.fetchone()
            
            if exists:
                # 1. Create a policy that allows the DB user to do EVERYTHING
                # We use TO PUBLIC or TO role_name. To be safe for the pooler, 
                # we grant it to the role explicitly used by Django.
                cursor.execute(f"""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_policies 
                            WHERE tablename = '{table}' AND policyname = 'django_owner_policy'
                        ) THEN
                            CREATE POLICY django_owner_policy ON public."{table}"
                            FOR ALL 
                            TO "{role_name}"
                            USING (true)
                            WITH CHECK (true);
                        END IF;
                    END $$;
                """)
                print(f"  [RLS] Added owner policy to public.{table} for role {role_name}")

def remove_owner_policies(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            cursor.execute(f'DROP POLICY IF EXISTS django_owner_policy ON public."{table}";')

class Migration(migrations.Migration):
    dependencies = [
        ("analyzer", "0006_unforce_rls"),
    ]

    operations = [
        migrations.RunPython(add_owner_policies, reverse_code=remove_owner_policies),
    ]
