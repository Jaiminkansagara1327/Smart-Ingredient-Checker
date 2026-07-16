"""
Migration: 0005_enable_rls_on_all_tables

WHY THIS EXISTS
---------------
Ingrexa uses Supabase as its PostgreSQL provider. Supabase exposes all tables
in the `public` schema through its built-in PostgREST REST API. Without Row
Level Security (RLS) enabled, **anyone** who knows the Supabase project URL
and the anon key can read every row in every table — including auth_user
(passwords!), django_session (session tokens!), and all analyzer data.

This migration enables RLS on every Django-managed table.

HOW RLS WORKS WITH DJANGO
--------------------------
- Django connects via psycopg2 using the DATABASE_URL (direct TCP to Postgres).
- Supabase's service-role connections have `BYPASSRLS` set, so Django is
  completely unaffected — all queries work exactly as before.
- The Supabase PostgREST API (used by Supabase JS/REST clients) does NOT
  bypass RLS, so with RLS enabled and NO permissive policies defined,
  PostgREST requests are denied by default (deny-all).

TABLES COVERED
--------------
Django core tables:
  django_migrations, django_content_type, django_admin_log, django_session

Django auth tables:
  auth_user, auth_user_groups, auth_user_user_permissions,
  auth_permission, auth_group, auth_group_permissions

Analyzer app tables:
  analyzer_contactmessage, analyzer_product, analyzer_userprofile,
  analyzer_searchevent, analyzer_productfavorite, analyzer_analysisrecord
"""

from django.db import migrations


# All tables that must have RLS enabled (matches the Supabase lint warnings).
_TABLES = [
    # Django internal / system tables
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "django_session",
    # Django auth tables
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "auth_permission",
    "auth_group",
    "auth_group_permissions",
    # Analyzer application tables
    "analyzer_contactmessage",
    "analyzer_product",
    "analyzer_userprofile",
    "analyzer_searchevent",
    "analyzer_productfavorite",
    "analyzer_analysisrecord",
]


def enable_rls(apps, schema_editor):
    # RLS is a PostgreSQL-only feature. Skip silently when using SQLite (local dev).
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = %s
                );
                """,
                [table],
            )
            (exists,) = cursor.fetchone()

            if not exists:
                print(f"  [RLS] Skipping '{table}' — table does not exist yet.")
                continue

            cursor.execute(
                f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;'
            )
            cursor.execute(
                f'ALTER TABLE public."{table}" FORCE ROW LEVEL SECURITY;'
            )
            print(f"  [RLS] Enabled RLS on public.{table}")


def disable_rls(apps, schema_editor):
    # RLS is a PostgreSQL-only feature. Skip silently when using SQLite (local dev).
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = %s
                );
                """,
                [table],
            )
            (exists,) = cursor.fetchone()

            if not exists:
                continue

            cursor.execute(
                f'ALTER TABLE public."{table}" NO FORCE ROW LEVEL SECURITY;'
            )
            cursor.execute(
                f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY;'
            )
            print(f"  [RLS] Disabled RLS on public.{table}")


class Migration(migrations.Migration):

    dependencies = [
        # Must run after the last analyzer migration that creates tables.
        ("analyzer", "0004_userprofile_searchevent_productfavorite_and_more"),
    ]

    operations = [
        migrations.RunPython(
            enable_rls,
            reverse_code=disable_rls,
        ),
    ]
