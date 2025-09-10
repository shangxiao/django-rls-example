from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.constraints import BaseConstraint

User = get_user_model()


class RawSQL(BaseConstraint):
    def __init__(self, *, name, sql, reverse_sql):
        super().__init__(name=name)
        self.sql = sql
        self.reverse_sql = reverse_sql

    def create_sql(self, model, schema_editor):
        return self.sql

    def remove_sql(self, model, schema_editor):
        return self.reverse_sql

    def constraint_sql(self, model, schema_editor):
        return None

    def validate(self, *args, **kwargs):
        return True

    def __eq__(self, other):
        if isinstance(other, RawSQL):
            return (
                self.name == other.name
                and self.sql == other.sql
                and self.reverse_sql == other.reverse_sql
            )
        return super().__eq__(other)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["sql"] = self.sql
        kwargs["reverse_sql"] = self.reverse_sql
        return path, args, kwargs


# class CurrentUser(models.Model):
#     username = models.CharField()
#
#     class Meta:
#         managed = False


class Account(models.Model):
    name = models.CharField()

    class Meta:
        db_rls = True
        # db_rls_condition = "exists (select 1 from rls_accountaccess auth where auth.user_id = current_user::int and auth.account_id = rls_account.id)"
        db_rls_condition = "exists (select 1 from rls_accountaccess auth where auth.user_id = nullif(current_setting('app.user', true), '')::int and auth.account_id = rls_account.id)"

    def __str__(self):
        return self.name


class AccountAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    class Meta:
        unique_together = [
            ("user", "account"),
        ]
