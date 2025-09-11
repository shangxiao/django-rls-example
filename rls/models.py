from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.expressions import Exists, Func, OuterRef

User = get_user_model()


class AccountAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey("Account", on_delete=models.CASCADE)

    class Meta:
        unique_together = [
            ("user", "account"),
        ]


class AppUser(Func):
    template = "nullif(current_setting('app.user', true), '')::int"
    output_field = models.IntegerField()


class Account(models.Model):
    name = models.CharField()

    class Meta:
        pass
        db_rls = True
        # some raw examples?
        # db_rls_condition = "exists (select 1 from rls_accountaccess auth where auth.user_id = current_user::int and auth.account_id = rls_account.id)"
        # db_rls_condition = "exists (select 1 from rls_accountaccess auth where auth.user_id = nullif(current_setting('app.user', true), '')::int and auth.account_id = rls_account.id)"

        # (the lambda is because we can't construct a querset with related references until apps are ready, only simple querysets)
        db_rls_condition = lambda: Exists(  # noqa
            AccountAccess.objects.filter(user_id=AppUser(), account=OuterRef("pk"))
        )

    def __str__(self):
        return self.name
