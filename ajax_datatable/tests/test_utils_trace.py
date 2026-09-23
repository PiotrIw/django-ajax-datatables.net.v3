"""
trace()/prettyprint_query()/prettyprint_queryset() are debug-output helpers
that branch on whether optional packages (termcolor, pygments) are
installed. Rather than depend on what happens to be present in the test
environment, the "package is available" branches are exercised by patching
the module-level names utils.py binds them to - the same names the
try/except ImportError blocks at import time would leave unset.
"""
import importlib
import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest import mock

import ajax_datatable.utils as utils_module
from ajax_datatable.utils import prettyprint_query, prettyprint_queryset, trace


class TraceTestCase(unittest.TestCase):

    def test_plain_message_is_printed(self):
        out = io.StringIO()
        with redirect_stdout(out):
            trace('hello')
        self.assertIn('hello', out.getvalue())

    def test_prettify_uses_pformat(self):
        out = io.StringIO()
        with redirect_stdout(out):
            trace({'a': 1}, prettify=True)
        self.assertIn("'a': 1", out.getvalue())

    def test_prompt_is_prefixed_to_the_message(self):
        out = io.StringIO()
        with redirect_stdout(out):
            trace('hello', prompt='greeting')
        self.assertIn('greeting', out.getvalue())
        self.assertIn('hello', out.getvalue())

    def test_uses_termcolor_when_available(self):
        fake_termcolor = mock.MagicMock()
        with mock.patch('ajax_datatable.utils.termcolor', fake_termcolor):
            trace('hello', color='red')
        fake_termcolor.cprint.assert_called_once()


class PrettyprintQueryTestCase(unittest.TestCase):

    def test_prints_formatted_sql(self):
        out = io.StringIO()
        with redirect_stdout(out):
            prettyprint_query('select * from foo', colorize=False, prettify=True)
        self.assertIn('SELECT', out.getvalue().upper())

    def test_without_prettify_prints_the_raw_sql(self):
        out = io.StringIO()
        with redirect_stdout(out):
            prettyprint_query('select 1', colorize=False, prettify=False)
        self.assertIn('select 1', out.getvalue())

    def test_colorize_uses_pygments_when_available(self):
        fake_pygments = mock.MagicMock()
        fake_pygments.highlight.return_value = 'HIGHLIGHTED-SQL'
        with mock.patch('ajax_datatable.utils.pygments', fake_pygments), \
                mock.patch('ajax_datatable.utils.SqlLexer', mock.MagicMock(), create=True), \
                mock.patch('ajax_datatable.utils.TerminalTrueColorFormatter', mock.MagicMock(), create=True):
            out = io.StringIO()
            with redirect_stdout(out):
                prettyprint_query('select 1', colorize=True, prettify=False)
        fake_pygments.highlight.assert_called_once()
        self.assertIn('HIGHLIGHTED-SQL', out.getvalue())

    def test_prettyprint_queryset_uses_the_query_string(self):
        class DummyQuery:
            def __str__(self):
                return 'SELECT 1'

        class DummyQuerySet:
            query = DummyQuery()

        out = io.StringIO()
        with redirect_stdout(out):
            prettyprint_queryset(DummyQuerySet(), colorize=False, prettify=False)
        self.assertIn('SELECT 1', out.getvalue())


class OptionalDependencyFallbackTestCase(unittest.TestCase):
    """
    utils.py shims sqlparse with a no-op stub when it isn't installed, and
    only imports pygments-based colorizing when it *is* - reloading the
    module is the only way to exercise either non-default path, since each
    one only runs given a package-availability state that doesn't match
    what's actually installed in this test environment (sqlparse: present;
    pygments: absent). `sys.modules[name] = None` is Python's documented way
    to force the next `import name` to raise ImportError, used to simulate
    sqlparse's absence; a fake module tree injected into sys.modules
    simulates pygments' presence for the opposite case. Reloading only
    rebinds names inside utils_module itself - other modules already hold
    their own references from `from .utils import X` and are unaffected -
    but utils_module is reloaded back to its real state afterward
    regardless, for every other test's sake.
    """

    def test_sqlparse_fallback_stub_when_package_is_unavailable(self):
        with mock.patch.dict(sys.modules, {'sqlparse': None}):
            importlib.reload(utils_module)
            try:
                self.assertEqual(utils_module.sqlparse.format('SELECT 1', reindent=True), 'SELECT 1')
            finally:
                importlib.reload(utils_module)

    def test_pygments_is_imported_when_the_package_is_available(self):
        fake_pygments = types.ModuleType('pygments')
        fake_lexers = types.ModuleType('pygments.lexers')
        fake_lexers.SqlLexer = type('SqlLexer', (), {})
        fake_formatters = types.ModuleType('pygments.formatters')
        fake_formatters.TerminalTrueColorFormatter = type('TerminalTrueColorFormatter', (), {})

        with mock.patch.dict(sys.modules, {
            'pygments': fake_pygments,
            'pygments.lexers': fake_lexers,
            'pygments.formatters': fake_formatters,
        }):
            importlib.reload(utils_module)
            try:
                self.assertIs(utils_module.pygments, fake_pygments)
                self.assertIs(utils_module.SqlLexer, fake_lexers.SqlLexer)
                self.assertIs(utils_module.TerminalTrueColorFormatter, fake_formatters.TerminalTrueColorFormatter)
            finally:
                importlib.reload(utils_module)
