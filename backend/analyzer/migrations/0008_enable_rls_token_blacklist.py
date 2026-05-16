"""
Migration: 0008_enable_rls_token_blacklist

WHY THIS EXISTS
---------------
Supabase flagged the token blacklist tables as publicly exposed because they are in 
the `public` schema and did not have Row Level Security (RLS) enabled.

This migration:
1. Enables RLS on `token_blacklist_outstandingtoken` and `token_blacklist_blacklistedtoken`.
2. Adds a 'django_owner_policy' that allows the 'postgres' role (used by Django) 
   to perform all operations.
3. Since no permissive policies are added for 'anon' or 'authenticated' roles, 
   the Supabase PostgREST API will be denied access by default, satisfying 
   the security requirement.
"""
from django.db import connection
from django.db import migrations

_TABLES = [
    "token_blacklist_outstandingtoken",
    "token_blacklist_blacklistedtoken",
]

def enable_rls_and_add_policy(apps, schema_editor):
    if connection.vendor == "sqlite":
        return
    role_name = 'postgres'

    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            # 1. Check if table exists
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);",
                [table]
            )
            (exists,) = cursor.fetchone()
            
            if exists:
                # 2. Enable RLS
                cursor.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;')
                
                # 3. Create a policy that allows the DB user to do EVERYTHING
                # This is required because Supabase pooler (port 6543) does not bypass RLS.
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
                print(f"  [RLS] Enabled RLS and added owner policy to public.{table}")
            else:
                print(f"  [RLS] Skipping '{table}' — table does not exist.")

def disable_rls_and_remove_policy(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for table in _TABLES:
            cursor.execute(f'DROP POLICY IF EXISTS django_owner_policy ON public."{table}";')
            cursor.execute(f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY;')

class Migration(migrations.Migration):
    dependencies = [
        ("analyzer", "0007_add_postgres_policy"),
    ]

    operations = [
        migrations.RunPython(enable_rls_and_add_policy, reverse_code=disable_rls_and_remove_policy),
    ]
