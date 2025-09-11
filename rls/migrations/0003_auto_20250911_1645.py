import rls.db_utils
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rls", "0002_initial"),
    ]

    operations = [
        rls.db_utils.AlterRLS(
            model_name="account",
            db_rls=True,
        ),
        rls.db_utils.CreatePolicy(
            model_name="account",
            db_rls_condition='EXISTS(SELECT 1 AS "a" FROM "rls_accountaccess" U0 WHERE (U0."account_id" = ("rls_account"."id") AND U0."user_id" = (nullif(current_setting(\'app.user\', true), \'\')::int)) LIMIT 1)',
        ),
    ]
