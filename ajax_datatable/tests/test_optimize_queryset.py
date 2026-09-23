from django.db import models
import unittest
from ajax_datatable import AjaxDatatableView


class OptOwner(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = 'myappname3'


class OptRelated(models.Model):
    name = models.CharField(max_length=20)
    owner = models.ForeignKey(OptOwner, null=True, on_delete=models.CASCADE)

    class Meta:
        app_label = 'myappname3'


class OptMain(models.Model):
    title = models.CharField(max_length=20)
    related = models.ForeignKey(OptRelated, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(OptRelated, related_name='tagged')

    class Meta:
        app_label = 'myappname3'


class OptView(AjaxDatatableView):
    model = OptMain
    column_defs = [
        {'name': 'id', 'visible': False},
        {'name': 'title'},
        {'name': 'related_name', 'foreign_field': 'related__name'},
        {'name': 'tags_name', 'm2m_foreign_field': 'tags__name', 'searchable': False, 'orderable': False},
    ]


class OptBadM2mView(AjaxDatatableView):
    model = OptMain
    column_defs = [
        {'name': 'id', 'visible': False},
        # a resolvable, but 3-level, path: valid enough for column construction
        # to succeed, so the "2 level max" check in optimize_queryset() itself
        # is what actually raises here
        {'name': 'bad', 'm2m_foreign_field': 'tags__owner__name'},
    ]


class OptimizeQuerysetTestCase(unittest.TestCase):
    """
    optimize_queryset() only builds a QuerySet (select_related/prefetch_related/
    only are all lazy query-builder calls), so this never touches the database.
    """

    def test_select_related_prefetch_related_and_only_are_applied(self):
        view = OptView()
        view.initialize(None)
        qs = view.get_initial_queryset()
        optimized = view.optimize_queryset(qs)

        self.assertIn('related', optimized.query.select_related)

        prefetch_lookups = [
            getattr(lookup, 'prefetch_through', lookup)
            for lookup in optimized._prefetch_related_lookups
        ]
        self.assertIn('tags', prefetch_lookups)

        deferred_fields, defer = optimized.query.deferred_loading
        self.assertFalse(defer)  # only() was used: this is an allow-list, not a defer-list
        self.assertIn('title', deferred_fields)
        self.assertIn('related__name', deferred_fields)

    def test_m2m_foreign_field_must_be_two_levels(self):
        view = OptBadM2mView()
        view.initialize(None)
        qs = view.get_initial_queryset()
        with self.assertRaisesRegex(Exception, 'm2m_foreign_field should be 2 level max'):
            view.optimize_queryset(qs)
