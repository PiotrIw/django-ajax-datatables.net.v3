"""
Exercises AjaxDatatableView through an actual HTTP request/response cycle
(dispatch() / get() / read_parameters() / render_row_details()), which the
rest of the suite never does: every other test module instantiates the view
and calls its helper methods directly, bypassing dispatch() entirely.
"""
import json

from unittest import TestCase

import factory
import factory.random
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from ajax_datatable import AjaxDatatableView


User = get_user_model()


class HttpUserView(AjaxDatatableView):
    model = User
    # 'username' is given by name rather than numeric position, to exercise
    # fix_initial_order()'s name-to-index resolution.
    initial_order = [['username', 'asc']]
    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'id',
            'visible': False,
        }, {
            'name': 'username',
            'title': 'User Name',  # explicit title, bypassing the model-field lookup
        }, {
            # a callable initialSearchValue must be invoked and its result
            # (not the callable itself) sent back to the client
            'name': 'first_name',
            'initialSearchValue': lambda: 'called',
            'max_length': 4,  # short enough that most fake first names get clipped
        }, {
            'name': 'last_name',
        }, {
            'name': 'groups',
            'm2m_foreign_field': 'groups__name',
            'searchable': False,
            'orderable': False,
        }
    ]

    def get_latest_by(self, request):
        return 'date_joined'


class HttpUserAllOptimizationsDisabledView(AjaxDatatableView):
    model = User
    disable_queryset_optimization_only = True
    disable_queryset_optimization_select_related = True
    disable_queryset_optimization_prefetch_related = True
    column_defs = [
        {'name': 'id', 'visible': False},
        {'name': 'username'},
    ]


class HttpUserBadRowIdFieldnameView(AjaxDatatableView):
    model = User
    table_row_id_fieldname = 'does_not_exist'
    column_defs = [
        {'name': 'id', 'visible': False},
        {'name': 'username'},
    ]


class HttpUserBadInitialOrderColumnView(AjaxDatatableView):
    model = User
    initial_order = [[99, 'asc']]
    column_defs = [
        {'name': 'id', 'visible': False},
        {'name': 'username'},
    ]


class HttpUserNonOrderableInitialOrderView(AjaxDatatableView):
    model = User
    initial_order = [[1, 'asc']]
    column_defs = [
        {'name': 'id', 'visible': False},
        {'name': 'username', 'orderable': False},
    ]


class HttpUserIdInitialOrderView(AjaxDatatableView):
    """ 'id' is silently renamed to 'pk'; initial_order may still name it 'id'. """
    model = User
    initial_order = [['id', 'asc']]
    column_defs = [
        # visible=False columns are non-orderable by default; needs an explicit
        # override here so the initial-order sanity check in dispatch() passes
        {'name': 'id', 'visible': False, 'orderable': True},
        {'name': 'username'},
    ]


class HttpUserUnknownInitialOrderNameView(AjaxDatatableView):
    model = User
    initial_order = [['does_not_exist', 'asc']]
    column_defs = [
        {'name': 'id', 'visible': False},
        {'name': 'username'},
    ]


class HttpUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'httpuser_{}'.format(n))
    password = 'password'
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


def _bool(value):
    return 'true' if value else 'false'


def datatables_params(draw=1, start=0, length=10, columns=(), order=(), search_value=''):
    """
    Builds the bracket-notation query params DataTables sends on a draw
    request (see utils.js's serializeParams()).
    """
    params = {
        'draw': str(draw),
        'start': str(start),
        'length': str(length),
        'search[value]': search_value,
    }
    for i, col in enumerate(columns):
        base = 'columns[%d]' % i
        params[base + '[name]'] = col.get('name', '')
        params[base + '[data]'] = col.get('data', col.get('name', ''))
        params[base + '[searchable]'] = _bool(col.get('searchable', True))
        params[base + '[orderable]'] = _bool(col.get('orderable', True))
        params[base + '[search][value]'] = col.get('search', '')
    for i, (column_index, direction) in enumerate(order):
        params['order[%d][column]' % i] = str(column_index)
        params['order[%d][dir]' % i] = direction
    return params


class ViewHttpTestCase(TestCase):

    def setUp(self):
        factory.random.reseed_random('test_views_http')
        self.factory = RequestFactory()
        self.users = HttpUserFactory.create_batch(15)

    def tearDown(self):
        User.objects.all().delete()

    def _get(self, view_class, params, accept='application/json'):
        kwargs = {'HTTP_ACCEPT': accept} if accept else {}
        request = self.factory.get('/datatable/', data=params, **kwargs)
        return view_class.as_view()(request)

    def test_initialize_action(self):
        response = self._get(HttpUserView, {'action': 'initialize'})
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)

        names = [c['name'] for c in payload['columns']]
        self.assertIn('username', names)
        self.assertIn('pk', names)  # 'id' got renamed since no explicit 'pk' column

        first_name_col = next(c for c in payload['columns'] if c['name'] == 'first_name')
        self.assertEqual(first_name_col['initialSearchValue'], 'called')
        self.assertEqual(payload['searchCols'][names.index('first_name')]['search'], 'called')

        # the string-named initial_order position was resolved to a numeric index
        self.assertEqual(payload['order'], [[names.index('username'), 'asc']])

    def test_initialize_maps_id_to_pk_in_initial_order(self):
        response = self._get(HttpUserIdInitialOrderView, {'action': 'initialize'})
        payload = json.loads(response.content)
        names = [c['name'] for c in payload['columns']]
        self.assertEqual(payload['order'], [[names.index('pk'), 'asc']])

    def test_initialize_rejects_out_of_range_initial_order_column(self):
        with self.assertRaisesRegex(Exception, 'does not exists'):
            self._get(HttpUserBadInitialOrderColumnView, {'action': 'initialize'})

    def test_initialize_rejects_non_orderable_initial_order_column(self):
        with self.assertRaisesRegex(Exception, 'is not orderable'):
            self._get(HttpUserNonOrderableInitialOrderView, {'action': 'initialize'})

    def test_initialize_rejects_unknown_initial_order_name(self):
        with self.assertRaisesRegex(Exception, 'is invalid'):
            self._get(HttpUserUnknownInitialOrderNameView, {'action': 'initialize'})

    def test_details_action_without_custom_template(self):
        user = self.users[0]
        response = self._get(HttpUserView, {'action': 'details', 'pk': str(user.pk)})
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload['parent-row-id'], str(user.pk))
        self.assertIn(user.username, payload['html'])

    def test_non_ajax_request_is_rejected_by_dispatch(self):
        # dispatch() itself gates on request.accepts("application/json"); the
        # non-JSON branch is an unfinished "render_table" placeholder (see the
        # commented-out method below it) that just asserts False today.
        with self.assertRaises(AssertionError):
            self._get(HttpUserView, {'draw': '1', 'start': '0', 'length': '10'}, accept='text/html')

    def test_get_rejects_non_ajax_request_when_called_directly(self):
        # get()'s own is_ajax_request guard is unreachable through dispatch()
        # (which rejects non-JSON requests first, above), but stays meaningful
        # for a view method called directly.
        request = self.factory.get(
            '/datatable/', data={'draw': '1', 'start': '0', 'length': '10'}, HTTP_ACCEPT='text/html')
        response = HttpUserView().get(request)
        self.assertEqual(response.status_code, 400)

    def test_malformed_integer_param_returns_bad_request(self):
        response = self._get(HttpUserView, {'draw': 'not-a-number', 'start': '0', 'length': '10'})
        self.assertEqual(response.status_code, 400)

    def test_draw_request_filters_orders_and_paginates(self):
        target = self.users[0]
        columns = [
            {'name': ''},
            {'name': 'pk', 'searchable': False, 'orderable': False},
            {'name': 'username', 'search': target.username},
            {'name': 'first_name'},
            {'name': 'last_name'},
            {'name': 'groups', 'searchable': False, 'orderable': False},
        ]
        params = datatables_params(draw=7, start=0, length=10, columns=columns, order=[[2, 'desc']])
        response = self._get(HttpUserView, params)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)

        self.assertEqual(payload['draw'], 7)
        self.assertEqual(payload['recordsTotal'], 1)
        self.assertEqual(payload['recordsFiltered'], 1)
        self.assertEqual(len(payload['data']), 1)
        self.assertEqual(payload['data'][0]['username'], target.username)

    def test_length_minus_one_returns_all_rows(self):
        columns = [{'name': 'pk'}, {'name': 'username'}]
        params = datatables_params(draw=1, start=0, length=-1, columns=columns)
        response = self._get(HttpUserView, params)
        payload = json.loads(response.content)
        self.assertEqual(len(payload['data']), len(self.users))

    def test_global_search_across_columns(self):
        target = self.users[0]
        columns = [{'name': 'pk'}, {'name': 'username'}, {'name': 'first_name'}, {'name': 'last_name'}]
        params = datatables_params(draw=1, start=0, length=10, columns=columns, search_value=target.username)
        response = self._get(HttpUserView, params)
        payload = json.loads(response.content)
        self.assertEqual(payload['recordsFiltered'], 1)
        self.assertEqual(payload['data'][0]['username'], target.username)

    def test_post_is_treated_like_get(self):
        columns = [{'name': 'pk'}, {'name': 'username'}]
        params = datatables_params(draw=1, start=0, length=-1, columns=columns)
        request = self.factory.post('/datatable/', data=params, HTTP_ACCEPT='application/json')
        response = HttpUserView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(len(payload['data']), len(self.users))

    def test_date_range_filters_rows(self):
        target = self.users[0]
        joined_on = target.date_joined.date().isoformat()
        columns = [{'name': 'pk'}, {'name': 'username'}]
        params = datatables_params(draw=1, start=0, length=-1, columns=columns)
        params['date_from'] = joined_on
        params['date_to'] = joined_on
        response = self._get(HttpUserView, params)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        # every factory-created user was created "now", so all of them fall
        # inside [joined_on, joined_on]
        self.assertEqual(len(payload['data']), len(self.users))

    def test_optimizations_can_be_fully_disabled(self):
        columns = [{'name': 'pk'}, {'name': 'username'}]
        params = datatables_params(draw=1, start=0, length=-1, columns=columns)
        response = self._get(HttpUserAllOptimizationsDisabledView, params)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(len(payload['data']), len(self.users))

    def test_get_table_row_id_falls_back_to_empty_string_on_bad_fieldname(self):
        columns = [{'name': 'pk'}, {'name': 'username'}]
        params = datatables_params(draw=1, start=0, length=10, columns=columns)
        response = self._get(HttpUserBadRowIdFieldnameView, params)
        payload = json.loads(response.content)
        self.assertNotIn('DT_RowId', payload['data'][0])

    def test_clip_value_as_plain_text(self):
        view = HttpUserView()
        self.assertEqual(view.clip_value('short', 10, False), 'short')
        self.assertEqual(view.clip_value('a-long-piece-of-text', 5, False), 'a-lon…')
