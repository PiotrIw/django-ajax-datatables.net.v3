
import datetime
import unittest

from django.db.models import CharField, DateField, DateTimeField, Q

from ajax_datatable.columns import Column
from ajax_datatable.filters import build_column_filter


class ColumnFilterTest(unittest.TestCase):
    def test_build_column_filter(self):
        model_field = CharField()
        column = Column(model_field=model_field, sort_field="fooo")
        column_spec = {
            'lookup_field': "foo",
        }
        filters = build_column_filter("foo", column, column_spec, "bar", True)
        self.assertEqual(filters, Q(fooofoo='bar'))

    def test_build_column_filter_multiple_field(self):
        """ Search for multiple fields """
        model_field = CharField(choices=[("foo", "boo"), ("far", "bar")])
        column = Column(model_field=model_field, sort_field="fooo")
        column_spec = {
            'lookup_field': "foo",
            'choices': "foo",
        }
        filters = build_column_filter("foo", column, column_spec, ["bar", "boo"], True)
        self.assertEqual(filters, Q(fooo__in=["far", "foo"]))

    def test_build_column_filter_choices_column_level_uses_raw_value(self):
        """
        Column-level filtering (not global) over a choices field means a select
        box was used client-side: the search value is already the stored key,
        not a label to look up.
        """
        model_field = CharField(choices=[("foo", "boo"), ("far", "bar")])
        column = Column(model_field=model_field, sort_field="fooo")
        column_spec = {
            'lookup_field': "foo",
            'choices': ["foo", "far"],
        }
        filters = build_column_filter("foo", column, column_spec, "far", False)
        self.assertEqual(filters, Q(fooo__in=["far"]))

    def test_build_column_filter_multiple_values_non_choice_field(self):
        """ Multiple search values (search_values_separator split) get ORed. """
        model_field = CharField()
        column = Column(model_field=model_field, sort_field="fooo")
        column_spec = {'lookup_field': "__icontains"}
        filters = build_column_filter("foo", column, column_spec, ["aaa", "bbb"], True)
        self.assertEqual(filters, Q(fooo__icontains="aaa") | Q(fooo__icontains="bbb"))

    def test_build_column_filter_date_field(self):
        model_field = DateField()
        column = Column(model_field=model_field, sort_field="created")
        filters = build_column_filter("created", column, {}, "01/15/2026", True)
        self.assertEqual(filters, Q(created__range=["2026-01-15", "2026-01-15"]))

    def test_build_column_filter_datetime_field(self):
        """ DateTimeField needs a __date__range lookup to drop the time part. """
        model_field = DateTimeField()
        column = Column(model_field=model_field, sort_field="created_at")
        filters = build_column_filter("created_at", column, {}, "01/15/2026", True)
        self.assertEqual(filters, Q(created_at__date__range=["2026-01-15", "2026-01-15"]))

    def test_build_column_filter_date_field_invalid_input_clears_results(self):
        """
        An unparsable (e.g. still-being-typed) date value falls back to an
        impossible date, so the table shows no matches rather than erroring.
        """
        model_field = DateField()
        column = Column(model_field=model_field, sort_field="created")
        filters = build_column_filter("created", column, {}, "not-a-date", True)
        impossible_date = datetime.date(1, 1, 1).isoformat()
        self.assertEqual(filters, Q(created__range=[impossible_date, impossible_date]))
