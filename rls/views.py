from contextlib import contextmanager

from django.db import connection, connections, transaction
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from rls.models import Account


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class AccountListView(ListView):
    model = Account


# Notes
#  - FORCE ROW LEVEL SECURITY must be used for table owners
#  - roles can bypass RLS
#    - need to make sure role nor group has bypass rls set
#    - leser role needs create, login and grant all privileges on all tables
#  - RLS seems to be an all-or-nothing approach
#    - how would you switch on/off RLS for a single DB user/connection
#    - not helpful? https://stackoverflow.com/a/60299762
#  - PG parameters are a bit iffy
#    - current_setting(..., 't') returns null
#    - RESET makes it "" because params can't be null?
#    - calling reset on db initialisation (migrations) makes this consistent
#
# Maybe what's needed is 2 DB connections: one regular and one restricted for user access?
#
# DATABASE_ROUTERS help? https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-DATABASE_ROUTERS
#  - Django expects connections to be different DBs
#  - eg test framework, it pauses - presumably trying to destroy DB but connection 2 still open so connection 1 pauses and times out
#
# Check persistent connections: https://docs.djangoproject.com/en/5.1/ref/databases/#persistent-connections
#
# SET ROLE?
#
# when authorising, need to consider when evaluated, ie lazy qs eval
#
# when creating 2 users, the RLS-based user need perms Django requires for not only the db but also the test db


@contextmanager
def authenticate(username):
    with connection.cursor() as cursor:
        cursor.execute(f"SET my.username = '{username}'")
        yield
        cursor.execute("RESET my.username")


@contextmanager
def authenticate_id(user_id):
    with connections["rls"].cursor() as cursor:
        print(f"SET my.user_id = '{user_id}'")
        cursor.execute(f"SET my.user_id = '{user_id}'")
        yield
        print("RESET my.user_id")
        cursor.execute("RESET my.user_id")


@contextmanager
def disable_auth():
    # some sort of role switching or bypassing of RLS
    #  - SET ROLE
    #  - ALTER ROLE BYPASSRLS
    yield


def get_owner_transaction():
    with connection.cursor() as cursor:
        with transaction.atomic():
            cursor.execute("SET LOCAL my.username = 'owner'")
            cursor.execute("SHOW my.username")
            row = cursor.fetchone()
            owner = row[0]
            return owner


def get_owner():
    with connection.cursor() as cursor:
        # cursor.execute("SET my.username = 'owner'")
        cursor.execute("SHOW my.username")
        row = cursor.fetchone()
        owner = row[0]
        return owner


def view(request):
    # owner_0 = get_owner()
    owner_0 = "xxx"
    with authenticate("derp"):
        owner_1 = get_owner()
    owner_2 = get_owner()
    return HttpResponse(f"owner: [{owner_0}] [{owner_1}] [{owner_2}]")
