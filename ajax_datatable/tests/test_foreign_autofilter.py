"""
Autofilter over a foreign_field column whose values live on a *different*
model than the view's own model. list_autofilter_choices() special-cases
this (field.model != self.model) and delegates to get_foreign_queryset(),
which no other test module exercises.
"""
from unittest import TestCase

import factory
import factory.random
from django.contrib.auth import get_user_model

from ajax_datatable import AjaxDatatableView
from user.models import Profile


User = get_user_model()


class ProfileAjaxDatatableView(AjaxDatatableView):
    model = Profile
    column_defs = [
        {'name': 'id', 'visible': False},
        {
            'name': 'owner_username',
            'foreign_field': 'owner__username',
            'choices': True,
            'autofilter': True,
        },
    ]


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'foreignautofilter_{}'.format(n))
    password = 'password'


class ProfileFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Profile

    owner = factory.SubFactory(UserFactory)
    bio = factory.Faker('sentence')


class ForeignAutofilterTestCase(TestCase):

    def setUp(self):
        factory.random.reseed_random('test_foreign_autofilter')
        self.profiles = ProfileFactory.create_batch(5)

    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.filter(username__startswith='foreignautofilter_').delete()

    def test_autofilter_over_a_foreign_field_uses_the_related_model(self):
        view = ProfileAjaxDatatableView()
        view.initialize(None)

        # get_foreign_queryset()'s default implementation is unfiltered
        # (field.model.objects.all()), so this only asserts our own users
        # are among the choices - not that they're the only ones - to stay
        # robust against whatever else exists in the shared database.
        choices = view.column_spec_by_name('owner_username')['choices']
        returned_usernames = {value for value, _label in choices}
        expected_usernames = {p.owner.username for p in self.profiles}
        self.assertTrue(expected_usernames.issubset(returned_usernames))
