# from django.test import TestCase
from unittest import TestCase
import factory
import factory.random
from django.contrib.auth import get_user_model
from ajax_datatable import AjaxDatatableView


User = get_user_model()


class UserAjaxDatatableView(AjaxDatatableView):
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'username',
        }, {
            'name': 'first_name',
            'choices': True,
            'autofilter': True,
        }, {
            'name': 'last_name',
        }
    ]


class UserDatatablesWithWrongKeyView(AjaxDatatableView):
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'username',
            'wrongkey': 'you_baaaad',
        }, {
            'name': 'first_name',
            'choices': True,
            'autofilter': True,
        }, {
            'name': 'last_name',
        }
    ]


class UserDatatablesWithEmptyColumnNameView(AjaxDatatableView):
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': '',
        }, {
            'name': 'first_name',
            'choices': True,
            'autofilter': True,
        }, {
            'name': 'last_name',
        }
    ]


class UserAutofilterBadMaxLengthView(AjaxDatatableView):
    """ A non-int max_length breaks list_autofilter_choices() internally. """
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'first_name',
            'choices': True,
            'autofilter': True,
            'max_length': None,
        }
    ]


class UserAutofilterWithInitialSearchValueView(AjaxDatatableView):
    """ initialSearchValue not among the distinct values must be appended. """
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'first_name',
            'choices': True,
            'autofilter': True,
            'initialSearchValue': 'ZzNotARealFirstName',
        }
    ]


class UserAutofilterDateJoinedView(AjaxDatatableView):
    """ Autofilter over a date field takes a different choices-formatting path. """
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'date_joined',
            'choices': True,
            'autofilter': True,
        }
    ]


class UserAutofilterClippedChoicesView(AjaxDatatableView):
    """ A positive max_length clips each autofilter choice's label. """
    model = User
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'first_name',
            'choices': True,
            'autofilter': True,
            'max_length': 3,
        }
    ]


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'username_{}'.format(n))
    password = 'password'
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class AutoFilterTestCase(TestCase):

    def setUp(self):
        factory.random.reseed_random('test_static_columns')
        self.build_fake_data()

    def tearDown(self):
        User.objects.all().delete()

    def build_fake_data(self):
        UserFactory.create_batch(100)

    def test_autofilter_columns(self):

        request = None
        view = UserAjaxDatatableView()
        view.initialize(request)
        print(view.column_spec_by_name('first_name'))

        # Since we activated 'autofilter' for 'first_name',
        # we should see a choices list filled with distinct values
        queryset = view.get_initial_queryset(request)
        names = queryset.values_list('first_name', flat=True).distinct().order_by('first_name')
        # Example:
        # [('Alicia', 'Alicia'), ('Amanda', 'Amanda'), ('Amy', 'Amy'), ...
        expected_choices = [(item, item) for item in names]

        self.assertSequenceEqual(expected_choices, view.column_spec_by_name('first_name')['choices'])

    def test_unexcpeted_key(self):

        request = None
        view = UserDatatablesWithWrongKeyView()

        with self.assertRaises(Exception) as raise_context:
            view.initialize(request)
        self.assertTrue('Unexpected key "wrongkey"' in str(raise_context.exception))
        print(str(raise_context.exception))

    def test_missing_column_name(self):
        """ There already is helper column with name ''. Should raise duplicate exception """
        request = None
        view = UserDatatablesWithEmptyColumnNameView()
        with self.assertRaisesRegex(Exception, 'Duplicate column name "" detected'):
            view.initialize(request)

    def test_autofilter_choices_exception_is_caught(self):
        """
        list_autofilter_choices() wraps its body in a try/except; a bad
        max_length (compared with '<= 0') is a convenient way to trigger it
        without mocking anything.
        """
        request = None
        view = UserAutofilterBadMaxLengthView()
        view.initialize(request)
        self.assertIsNone(view.column_spec_by_name('first_name')['choices'])

    def test_autofilter_appends_missing_initial_search_value(self):
        request = None
        view = UserAutofilterWithInitialSearchValueView()
        view.initialize(request)
        choices = view.column_spec_by_name('first_name')['choices']
        self.assertIn(('ZzNotARealFirstName', 'ZzNotARealFirstName'), choices)

    def test_autofilter_over_date_field(self):
        request = None
        view = UserAutofilterDateJoinedView()
        view.initialize(request)
        choices = view.column_spec_by_name('date_joined')['choices']
        self.assertTrue(len(choices) > 0)

    def test_autofilter_clips_long_choice_labels(self):
        request = None
        view = UserAutofilterClippedChoicesView()
        view.initialize(request)
        choices = view.column_spec_by_name('first_name')['choices']
        for value, label in choices:
            if len(value) > 3:
                self.assertTrue(label.endswith('…'))
