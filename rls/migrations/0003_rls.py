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
            db_rls_condition="exists (select 1 from rls_accountaccess auth where auth.user_id = nullif(current_setting('app.user', true), '')::int and auth.account_id = rls_account.id)",
        ),
    ]
