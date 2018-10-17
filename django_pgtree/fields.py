from django.db.models import Field, Lookup
from django.utils.translation import gettext_lazy as _


class LtreeField(Field):
    description = _("Dotted label path")

    def db_type(self, connection):
        return "ltree"

    def cast_db_type(self, connection):
        if self.max_length is None:
            return connection.ops.cast_char_field_without_max_length
        return super().cast_db_type(connection)

    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if isinstance(value, list) or value is None:
            return value
        if isinstance(value, str):
            return value.split(".")
        raise ValueError("Don't know how to handle {!r}".format(value))

    def get_prep_value(self, value):
        if isinstance(value, str) or value is None:
            return value
        return ".".join(value)

    def from_db_value(self, value, expression, connection):
        if not value:
            return []
        return value.split(".")


class BinaryLookup(Lookup):
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return " ".join((lhs, self.operator, rhs)), params


@LtreeField.register_lookup
class AncestorOf(BinaryLookup):
    lookup_name = "ancestor_of"
    operator = "@>"


@LtreeField.register_lookup
class DescendantOf(BinaryLookup):
    lookup_name = "descendant_of"
    operator = "<@"


@LtreeField.register_lookup
class MatchesLquery(BinaryLookup):
    lookup_name = "matches_lquery"
    operator = "~"
