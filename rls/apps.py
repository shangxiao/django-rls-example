from django.apps import AppConfig
from django.db.migrations.autodetector import registry
from django.db.models.options import DEFAULT_NAMES

from rls.db_utils import AlterRLS, CreatePolicy

DEFAULT_NAMES.update(["db_rls", "db_rls_condition"])


def rls_changes(app_label, model_name, from_model_state, to_model_state):
    operations = []

    if from_model_state.options.get("db_rls") != to_model_state.options.get("db_rls"):
        operations += [AlterRLS(model_name, to_model_state.options.get("db_rls"))]

    if not from_model_state.options.get(
        "db_rls_condition"
    ) and to_model_state.options.get("db_rls_condition"):
        operations += [
            CreatePolicy(model_name, to_model_state.options.get("db_rls_condition"))
        ]

    return operations if operations else None


registry.register(rls_changes)


class RlsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rls"
