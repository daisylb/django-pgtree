from django.contrib.postgres.operations import CreateExtension


class LtreeExtension(CreateExtension):
    """Django migration operation to add PostgreSQL extension LTree to our project."""

    def __init__(self):
        self.name = 'ltree'

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # No need to drop extension
        pass
