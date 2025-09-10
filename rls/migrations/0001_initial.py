from django.db import migrations


create_rls_role = """\
DO
$$
BEGIN
  IF NOT EXISTS (SELECT * FROM pg_user WHERE usename = 'rls') THEN
     CREATE ROLE rls WITH LOGIN NOBYPASSRLS;
     GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rls;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rls;
     GRANT SET ON PARAMETER "app.user" TO rls;
  END IF;
END
$$
;
"""

drop_rls_role = """\
DROP OWNED BY rls;
DROP ROLE rls;
"""


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=create_rls_role, reverse_sql=drop_rls_role, elidable=False
        ),
    ]
