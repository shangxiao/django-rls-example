import pytest
from django.db import connection, transaction

pytestmark = pytest.mark.django_db


def test_session_var():
    with connection.cursor() as cursor:
        with transaction.atomic():
            cursor.execute("SET LOCAL my.username = 'owner'")
        cursor.execute("SHOW my.username")
        row = cursor.fetchone()
        print(f"username: {row[0]}")

    with connection.cursor() as cursor:
        cursor.execute("SHOW my.username")
        row = cursor.fetchone()
        print(f"username: {row[0]}")
