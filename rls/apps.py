# import collections.abc
# from types import FunctionType
# from django.db.migrations.serializer import (
#     FUNCTION_TYPES,
#     BaseSerializer,
#     FunctionTypeSerializer,
#     Serializer,
#     serializer_factory,
# )
# from django.db.models import QuerySet
# from django.db.models.expressions import BaseExpression

from django.apps import AppConfig
from django.db import connection
from django.db.migrations.autodetector import registry
from django.db.models.options import DEFAULT_NAMES
from django.db.models.sql.query import Query
from rls.db_utils import AlterPolicy, AlterRLS, CreatePolicy, DropPolicy

DEFAULT_NAMES.update(["db_rls", "db_rls_condition"])


def rls_changes(
    app_label, model_name, from_state, to_state, from_model_state, to_model_state
):
    operations = []

    if (
        from_model_state.options.get("db_rls") if from_model_state else None
    ) != to_model_state.options.get("db_rls"):
        operations += [AlterRLS(model_name, to_model_state.options.get("db_rls"))]

    from_db_rls_condition = (
        from_model_state.options.get("db_rls_condition") if from_model_state else None
    )
    to_db_rls_condition = to_model_state.options.get("db_rls_condition")

    # render before passing to operation to avoid complex objects from being serialized

    if from_db_rls_condition:
        if callable(from_db_rls_condition):
            from_db_rls_condition = from_db_rls_condition()
            model = to_state.apps.get_model(app_label, model_name)
            query = Query(model=model)  # must alias_cols!
            where = query.build_where(from_db_rls_condition)
            compiler = query.get_compiler(connection=connection)
            using, params = where.as_sql(compiler, connection)
            with connection.cursor() as cur:
                from_db_rls_condition = cur.mogrify(using, params)

    if to_db_rls_condition:
        if callable(to_db_rls_condition):
            to_db_rls_condition = to_db_rls_condition()
            model = to_state.apps.get_model(app_label, model_name)
            query = Query(model=model)  # must alias_cols!
            where = query.build_where(to_db_rls_condition)
            compiler = query.get_compiler(connection=connection)
            using, params = where.as_sql(compiler, connection)
            with connection.cursor() as cur:
                to_db_rls_condition = cur.mogrify(using, params)

    if not from_db_rls_condition and to_db_rls_condition:
        operations += [CreatePolicy(model_name, to_db_rls_condition)]

    elif from_db_rls_condition and not to_db_rls_condition:
        operations += [DropPolicy(model_name, from_db_rls_condition)]

    elif from_db_rls_condition != to_db_rls_condition:
        operations += [AlterPolicy(model_name, to_db_rls_condition)]

    return operations if operations else None


registry.register(rls_changes)


# class ExpressionSerializer(BaseSerializer):
#     def serialize(self):
#         breakpoint()
#         pass
#
#
# class QuerySetSerializer(BaseSerializer):
#     def serialize(self):
#         from mogrify_queryset.models import mogrify_queryset
#
#         value, _ = serializer_factory(mogrify_queryset(self.value)).serialize()
#
#         return value, []
#
#
# class LambdaSerializer(FunctionTypeSerializer):
#     def serialize(self):
#         if self.value.__name__ == "<lambda>":
#             return serializer_factory(self.value()).serialize()
#         return super().serialize()


class RlsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rls"

    def ready(self):
        pass
        # unregister() should return the serializer
        # iterable_serializer = Serializer._registry.pop(collections.abc.Iterable)
        # Serializer.register(QuerySet, QuerySetSerializer)
        # Serializer.register(BaseExpression, ExpressionSerializer)
        # Serializer.register(collections.abc.Iterable, iterable_serializer)
        # Serializer._registry.pop(FUNCTION_TYPES)
        # Serializer.register(FunctionType, LambdaSerializer)
