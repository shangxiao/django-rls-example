from django.db import connection
from django.db.migrations.operations.base import Operation, OperationCategory


def set_config(param, value):
    if not connection.in_atomic_block:
        raise RuntimeError("Must be within atomic")

    with connection.cursor() as cursor:
        if value is None or value == "":
            cursor.execute("select set_config(%s, '', true)", [param])
            return

        cursor.execute("select current_setting(%s, true)", [param])
        curr_value = cursor.fetchone()[0]
        if curr_value == str(value):
            return
        elif curr_value is None or curr_value == "":
            cursor.execute("select set_config(%s, %s, true)", [param, str(value)])
        else:
            raise RuntimeError("Cannot change config within another config")


def enable_rls(schema_editor, model):
    table = schema_editor.quote_name(model._meta.db_table)
    schema_editor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def disable_rls(schema_editor, model):
    table = schema_editor.quote_name(model._meta.db_table)
    schema_editor.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def create_policy(schema_editor, policy_name, model, condition):
    # if condition is directly on model attrs then can build_where() like a check constraint
    # if condition is from a lookup table then build the full query
    table = schema_editor.quote_name(model._meta.db_table)
    using = condition
    schema_editor.execute(
        f"CREATE POLICY {schema_editor.quote_name(policy_name)} ON {table} USING ({using}) WITH CHECK ({using})"
    )


def drop_policy(schema_editor, policy_name, model):
    table = schema_editor.quote_name(model._meta.db_table)
    schema_editor.execute(
        f"DROP POLICY IF EXISTS {schema_editor.quote_name(policy_name)} ON {table}"
    )


def alter_policy(schema_editor, policy_name, model, condition):
    table = schema_editor.quote_name(model._meta.db_table)

    if isinstance(condition, str):
        using = condition

    schema_editor.execute(
        f"ALTER POLICY {schema_editor.quote_name(policy_name)} ON {table} USING ({using}) WITH CHECK ({using})"
    )


class AlterRLS(Operation):
    category = OperationCategory.ALTERATION

    def __init__(self, model_name, db_rls):
        self.model_name = model_name
        self.db_rls = db_rls

    def state_forwards(self, app_label, state):
        state.alter_model_options(app_label, self.model_name, {"db_rls": self.db_rls})

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # from_model = from_state.apps.get_model(app_label, self.model_name)
        to_model = to_state.apps.get_model(app_label, self.model_name)

        if getattr(to_model._meta, "db_rls", False):
            # schema_editor.enable_rls(to_model)
            enable_rls(schema_editor, to_model)
        else:
            # schema_editor.disable_rls(to_model)
            disable_rls(schema_editor, to_model)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        self.database_forwards(app_label, schema_editor, from_state, to_state)

    def describe(self):
        return "Alter Row Level Security"


class CreatePolicy(Operation):
    category = OperationCategory.ADDITION

    def __init__(self, model_name, db_rls_condition):
        self.model_name = model_name
        self.policy_name = model_name + "_policy"
        self.db_rls_condition = db_rls_condition

    def state_forwards(self, app_label, state):
        state.alter_model_options(
            app_label, self.model_name, {"db_rls_condition": self.db_rls_condition}
        )

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        if db_rls_condition := getattr(to_model._meta, "db_rls_condition", None):
            create_policy(schema_editor, self.policy_name, to_model, db_rls_condition)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        drop_policy(schema_editor, self.policy_name, to_model)

    def describe(self):
        return f"Create Policy {self.policy_name}"


class DropPolicy(Operation):
    category = OperationCategory.REMOVAL

    def __init__(self, model_name, db_rls_condition):
        self.model_name = model_name
        self.policy_name = model_name + "_policy"
        self.db_rls_condition = db_rls_condition

    def state_forwards(self, app_label, state):
        state.alter_model_options(
            app_label, self.model_name, {"db_rls_condition": None}
        )

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        drop_policy(schema_editor, self.policy_name, to_model)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        if db_rls_condition := getattr(to_model._meta, "db_rls_condition", None):
            create_policy(schema_editor, self.policy_name, to_model, db_rls_condition)

    def describe(self):
        return f"Drop Policy {self.policy_name}"


class AlterPolicy(Operation):
    category = OperationCategory.ALTERATION

    def __init__(self, model_name, db_rls_condition):
        self.model_name = model_name
        self.policy_name = model_name + "_policy"
        self.db_rls_condition = db_rls_condition

    def state_forwards(self, app_label, state):
        state.alter_model_options(
            app_label, self.model_name, {"db_rls_condition": self.db_rls_condition}
        )

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        alter_policy(schema_editor, self.policy_name, to_model, self.db_rls_condition)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        self.database_forwards(app_label, schema_editor, from_state, to_state)

    def describe(self):
        return f"Alter Policy {self.policy_name}"
