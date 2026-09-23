# from django.test import TestCase
from django.db import models
from django.db.models.functions import TruncDate
import unittest
from ajax_datatable import AjaxDatatableView


class TestModelWithoutLatestBy(models.Model):
    one = models.CharField(max_length=20)
    two = models.CharField(max_length=20)

    class Meta:
        app_label = 'myappname2'


class TestModelWithLatestBy(models.Model):
    one = models.CharField(max_length=20)
    two = models.CharField(max_length=20)

    class Meta:
        app_label = 'myappname2'
        get_latest_by = "one"


class TestModelWithHiddenLatestBy(models.Model):
    created = models.DateTimeField()
    one = models.CharField(max_length=20)

    class Meta:
        app_label = 'myappname2'
        get_latest_by = "-created"


class TestModelWithDateFieldLatestBy(models.Model):
    published = models.DateField()
    one = models.CharField(max_length=20)

    class Meta:
        app_label = 'myappname2'
        get_latest_by = "published"


class DatatablesWithoutLatestByView(AjaxDatatableView):
    model = TestModelWithoutLatestBy


class DatatablesWithLatestByView(AjaxDatatableView):
    model = TestModelWithLatestBy

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'one',
            'className': 'existing-class',  # 'latest_by' must be appended, not overwrite this
        }, {
            'name': 'two',
        }
    ]


class DatatablesWithHiddenLatestByView(AjaxDatatableView):
    model = TestModelWithHiddenLatestBy

    column_defs = [
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'one',
        }
    ]


class DatatablesForceFilterView(AjaxDatatableView):
    model = TestModelWithoutLatestBy

    def get_show_date_filters(self, request):
        return True


class DatatablesWithDateFieldLatestByView(AjaxDatatableView):
    model = TestModelWithDateFieldLatestBy

    column_defs = [
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'published',
        }, {
            'name': 'one',
        }
    ]


class DatatablesWithListLatestByView(AjaxDatatableView):
    model = TestModelWithoutLatestBy

    def get_latest_by(self, request):
        # get_latest_by() may return a list/tuple, as Meta.get_latest_by does
        return ['one']


class DateFiltersTestCase(unittest.TestCase):

    def test_filters_flag(self):

        request = None

        view = DatatablesWithoutLatestByView()
        view.initialize(request)
        self.assertIsNone(view.latest_by)
        self.assertFalse(view.show_date_filters)

        view = DatatablesWithLatestByView()
        view.initialize(request)
        self.assertIsNotNone(view.latest_by)
        self.assertTrue(view.show_date_filters)

        column_spec = view.column_spec_by_name(view.latest_by)
        self.assertIsNotNone(column_spec)
        self.assertIn('latest_by', column_spec.get('className', ''))

        view = DatatablesForceFilterView()
        view.initialize(request)
        self.assertTrue(view.show_date_filters)

    def test_date_range_filter_when_latest_by_is_not_a_column(self):
        """
        'latest_by' can be inherited from the model's Meta.get_latest_by, and
        then there is no reason for it to be one of the declared columns:
        filtering by date range used to raise AssertionError instead.
        """
        view = DatatablesWithHiddenLatestByView()
        view.initialize(None)
        self.assertEqual(view.latest_by, 'created')
        self.assertTrue(view.show_date_filters)
        self.assertNotIn(view.latest_by, view.column_index)

        qs = view.filter_queryset_by_date_range(
            '2026-01-01', '2026-01-31', TestModelWithHiddenLatestBy.objects.all())

        # the field is a DateTimeField, so the time part must be dropped from
        # both comparisons: that is what looking up the model field gives us
        conditions = qs.query.where.children
        self.assertEqual([c.lookup_name for c in conditions], ['gte', 'lte'])
        for condition in conditions:
            self.assertIsInstance(condition.lhs, TruncDate)

    def test_date_range_filter_with_plain_date_field(self):
        """
        A plain DateField latest_by (as opposed to DateTimeField) must not go
        through the DateTimeField-only TruncDate comparison.
        """
        view = DatatablesWithDateFieldLatestByView()
        view.initialize(None)

        qs = view.filter_queryset_by_date_range(
            '2026-01-01', '2026-01-31', TestModelWithDateFieldLatestBy.objects.all())

        conditions = qs.query.where.children
        self.assertEqual([c.lookup_name for c in conditions], ['gte', 'lte'])
        for condition in conditions:
            self.assertNotIsInstance(condition.lhs, TruncDate)

    def test_get_latest_by_accepts_a_list(self):
        view = DatatablesWithListLatestByView()
        view.initialize(None)
        self.assertEqual(view.latest_by, 'one')
