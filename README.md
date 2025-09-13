# django-rls-example

Postgres Row Level Security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html#DDL-ROWSECURITY

Toying with some ideas, something like

```python
class AccountAccess(Model):
    user = ForeignKey(User)
    account = ForeignKey("Account")

class AppUser(Func):
    template = "nullif(current_setting('app.user', true), '')::int"
    output_field = IntegerField()

class Account(Model):
    name = CharField()

    class Meta:
        # enables row level security
        db_rls = True

        # creates a policy
        # lambda here because Account isn't "ready" yet and we're attempting to access the account fk
        db_rls_condition = lambda: Exists(AccountAccess(account=OuterRef("pk"), user=AppUser()))


# from the console:

# for rls to work the "regular" connection must not be a superuser (see notes below, you can use a single connection as long as its not superuser and rls is "forced")
kfc = Account.objects.using("superuser").create(name="KFC")
mcd = Account.objects.using("superuser").create(name="McDonalds")
AccountAccess.objects.create(user=bob, account=kfc)

# params are either session-local or transaction-local meaning they clear automatically
# sessions are shared/long-lived for web apps so creating transaction local user id seems to be the "secure" way to set it and prevent leaking
# in practice though querysets are often evaluated during template rendering meaning this approach may not even be useful ¯\_(ツ)_/¯

with transaction.atomic():
    set_config('app.user', bob.pk)  # utility to create a transaction-local param
    print(Account.objects.values_list("name", flat=True))

<QuerySet ['KFC']>
```


### Notes

 - Tables must have row level security enabled & a policy created
 - RLS doesn't apply to roles with superuser
 - RLS only applies to roles for their own tables if RLS is "forced"

Possible approach this PoC is exploring:

 - Have 2 database connections in settings:
   - First: a superuser (or someone with create table permission) for migrations
   - Second: a standard app user who hasn't created the table and is not a superuser
 - 2 separate connections may not be necessary if the same user is not a superuser but has enough privileges to setup the database, however RLS must be forced
 - Examples show authorisation through custom parameter but similar approach can be done with roles & the `currentuser` identifier
   - The roles will need to be added/removed upon user management
   - The standard app user will need permissin to SET ROLE
 - Setting parameters isn't 100% secure imho as there's always the potential to "leak"
   - Roles are designed to be tied to connections whereas webapps reuse connections (or transactions)
   - Setting a parameter works in the same way as their lifetime is defined either by:
     - Session; or
     - Transaction
   - Setting a param or role within a session has no way of automatically resetting or expiring meaning that if you use this approach the application
     has to reset/clear it.  Bugs in code will mean users potentially seeing someone else's data.
   - Similarly for setting params/roles in a transaction.
   - The only way to automatically clear a param/role for a webapp with long-living connections appears to be:
     - Only set params/roles in a transaction
     - Only allow a single setting
     - Therefore wrapping any DB access with a transaction which may not be ideal for high volume

Further notes:

 - If using the transaction approach above then it will need to wrap around template rendering, if template contexts
   contain lazy querysets (and most likely will).
 - Using `ATOMIC_REQUESTS` will not help here: https://docs.djangoproject.com/en/5.2/topics/db/transactions/#tying-transactions-to-http-requests
 - Perhaps a custom middleware is what is required - but this will be causing unnecessary DB traffic for any request not
   requesting DB data
 - Custom connection to wrap in transaction?
 - Some discussion here about this sort of thing: https://www.reddit.com/r/PostgreSQL/comments/1jd7srp/costrisk_of_putting_every_query_in_an_explicit/
