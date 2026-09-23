"""
Direct unit coverage for ajax_datatable/columns.py. Column/ForeignColumn/
ManyToManyColumn.get_foreign_value() only need *some* object with the right
attributes, not a real saved row - so most of this runs against plain
SimpleNamespace/fake objects rather than the database, exactly like
get_foreign_value() itself is written to tolerate (getattr with fallbacks).
"""
import datetime
import unittest
from types import SimpleNamespace

from django.db import models

from ajax_datatable.columns import (
    Column, ColumnLink, ForeignColumn, ManyToManyColumn, Order, PlaceholderColumnLink,
)
from ajax_datatable.exceptions import ColumnOrderError


class RelatedModel(models.Model):
    label = models.CharField(max_length=20)

    class Meta:
        app_label = 'columns_tests'


class TagModel(models.Model):
    label = models.CharField(max_length=20, choices=[('a', 'Alpha'), ('b', 'Beta')])

    class Meta:
        app_label = 'columns_tests'


class MainModel(models.Model):
    title = models.CharField(max_length=20)
    related = models.ForeignKey(RelatedModel, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(TagModel)

    class Meta:
        app_label = 'columns_tests'


class _FakeManager:
    def __init__(self, items):
        self._items = items

    def get_queryset(self):
        return self._items


class _FakeRelated:
    def __init__(self, label):
        self.label = label


class ColumnTestCase(unittest.TestCase):

    def test_parse_choices_handles_single_element_tuples(self):
        column = Column(model_field=models.CharField())
        self.assertEqual(column.parse_choices([('solo',)]), {'solo': 'solo'})

    def test_string_tags_in_case_passes_through_none(self):
        column = Column(model_field=models.CharField())
        self.assertIsNone(column.string_tags_in_case(None))

    def test_render_column_value_uses_choices_lookup(self):
        model_field = models.CharField(choices=[('a', 'Alpha'), ('b', 'Beta')])
        column = Column(model_field=model_field)
        self.assertEqual(column.render_column_value(None, 'a'), 'Alpha')
        self.assertEqual(column.render_column_value(None, 'missing'), '')

    def test_render_column_value_formats_datetime(self):
        column = Column(model_field=models.DateTimeField())
        # just confirm it renders to a non-empty string rather than crashing;
        # exact formatting is covered by test_date_localization.py
        result = column.render_column_value(None, datetime.datetime(2026, 3, 7, 12, 30))
        self.assertTrue(result)

    def test_render_column_value_formats_date(self):
        column = Column(model_field=models.DateField())
        result = column.render_column_value(None, datetime.date(2026, 3, 7))
        self.assertTrue(result)

    def test_render_column_value_formats_boolean(self):
        column = Column(model_field=models.BooleanField())
        self.assertEqual(str(column.render_column_value(None, True)), 'Yes')
        self.assertEqual(str(column.render_column_value(None, False)), 'No')

    def test_render_column_falls_back_to_placeholder_on_missing_attribute(self):
        column = Column(model_field=models.CharField())
        column.name = 'does_not_exist'
        self.assertEqual(column.render_column(SimpleNamespace()), '???')

    def test_search_in_choices_without_choices_returns_empty(self):
        column = Column(model_field=models.CharField())
        self.assertEqual(column.search_in_choices('anything'), [])

    def test_search_in_choices_accepts_a_single_pattern(self):
        model_field = models.CharField(choices=[('a', 'Alpha'), ('b', 'Beta')])
        column = Column(model_field=model_field)
        self.assertEqual(column.search_in_choices('al'), ['a'])


class ForeignColumnTestCase(unittest.TestCase):

    def test_get_field_search_path(self):
        column = ForeignColumn('related_label', MainModel, 'related__label')
        self.assertEqual(column.get_field_search_path(), 'related__label')

    def test_get_foreign_field_raises_for_unknown_intermediate_field(self):
        with self.assertRaisesRegex(KeyError, "does_not_exist"):
            ForeignColumn('x', MainModel, 'does_not_exist__label')

    def test_get_foreign_value_direct_attribute_access(self):
        column = ForeignColumn('related_label', MainModel, 'related__label')
        obj = SimpleNamespace(related=SimpleNamespace(label='hello'))
        self.assertEqual(column.get_foreign_value(obj), 'hello')

    def test_get_foreign_value_uses_get_queryset_fallback(self):
        column = ForeignColumn('tags_label', MainModel, 'tags__label')
        obj = SimpleNamespace(tags=_FakeManager([_FakeRelated('a'), _FakeRelated('b')]))
        self.assertEqual(column.get_foreign_value(obj), ['a', 'b'])

    def test_get_foreign_value_falls_back_to_plain_iteration(self):
        column = ForeignColumn('tags_label', MainModel, 'tags__label')
        obj = SimpleNamespace(tags=[_FakeRelated('a'), _FakeRelated('b')])
        self.assertEqual(column.get_foreign_value(obj), ['a', 'b'])

    def test_get_foreign_value_returns_none_when_unresolvable(self):
        column = ForeignColumn('tags_label', MainModel, 'tags__label')
        obj = SimpleNamespace(tags=42)
        self.assertIsNone(column.get_foreign_value(obj))

    def test_get_foreign_value_stringifies_a_resolved_model_instance(self):
        column = ForeignColumn('related', MainModel, 'related')
        related_instance = RelatedModel(label='hello')
        obj = SimpleNamespace(related=related_instance)
        self.assertEqual(column.get_foreign_value(obj), str(related_instance))


class ManyToManyColumnTestCase(unittest.TestCase):

    def test_falls_back_to_all_when_nothing_was_prefetched(self):
        column = ManyToManyColumn('tags_label', MainModel, 'tags__label')

        class _AllManager:
            def all(self):
                return [_FakeRelated('x'), _FakeRelated('y')]

        obj = SimpleNamespace(tags=_AllManager())  # no 'tags_list' attribute
        self.assertEqual(column.get_foreign_value(obj), ['x', 'y'])

    def test_render_column_value_uses_choices_lookup(self):
        column = ManyToManyColumn('tags_label', MainModel, 'tags__label')
        self.assertTrue(column.has_choices_available)
        result = column.render_column_value(None, ['a', 'b', 'unknown'])
        self.assertEqual(result, 'Alpha, Beta, ')


class ColumnLinkTestCase(unittest.TestCase):

    def test_repr(self):
        model_column = Column(model_field=models.CharField())
        link = ColumnLink('foo', model_column, searchable='true', orderable='false', search_value='bar')
        self.assertIn('foo', repr(link))
        self.assertIn('bar', repr(link))

    def test_get_value_delegates_to_the_model_column(self):
        model_field = models.CharField()
        model_column = Column(model_field=model_field)
        model_column.name = 'title'
        link = ColumnLink('title', model_column)
        self.assertEqual(link.get_value(SimpleNamespace(title='hello')), 'hello')

    def test_to_dict_excludes_private_attributes(self):
        model_column = Column(model_field=models.CharField())
        link = ColumnLink('foo', model_column, search_value='bar')
        as_dict = link.to_dict()
        self.assertNotIn('_model_column', as_dict)
        self.assertEqual(as_dict['name'], 'foo')
        self.assertEqual(as_dict['search_value'], 'bar')


class PlaceholderColumnLinkTestCase(unittest.TestCase):

    def test_get_value_is_always_none(self):
        self.assertIsNone(PlaceholderColumnLink().get_value(SimpleNamespace()))


class OrderTestCase(unittest.TestCase):

    def test_get_order_mode_ascending_and_descending(self):
        model_column = Column(model_field=models.CharField())
        model_column.sort_column_name = 'title'
        link = ColumnLink('title', model_column)
        self.assertEqual(Order(0, 'asc', [link]).get_order_mode(), 'title')
        self.assertEqual(Order(0, 'desc', [link]).get_order_mode(), '-title')

    def test_repr(self):
        model_column = Column(model_field=models.CharField())
        link = ColumnLink('title', model_column)
        self.assertIn('title', repr(Order(0, 'asc', [link])))

    def test_raises_for_a_missing_key_when_column_links_is_dict_like(self):
        # Order() only ever indexes column_links_list with [...]; a real caller
        # always passes a list (where an out-of-range index raises IndexError,
        # not KeyError), but nothing in Order's own contract requires that -
        # this exercises its KeyError handling directly against a mapping.
        with self.assertRaises(ColumnOrderError):
            Order(5, 'asc', {0: PlaceholderColumnLink()})
