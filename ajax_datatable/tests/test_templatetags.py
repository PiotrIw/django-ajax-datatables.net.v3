"""
model_verbose_name/model_verbose_name_plural/model_name/app_label/testhasperm
are plain functions and can be called directly; ifhasperm is a custom block
tag, whose parsing only actually runs when a real template containing it is
compiled - so that half is exercised via django.template.Template/Context
rather than by calling the tag-compiler function with hand-built tokens.
"""
from types import SimpleNamespace
from unittest import TestCase

from django.contrib.auth import get_user_model
from django.template import Context, Template, TemplateSyntaxError

from ajax_datatable.templatetags.ajax_datatable_tags import (
    app_label, model_name, model_verbose_name, model_verbose_name_plural, testhasperm,
)


User = get_user_model()


class ModelFilterTagsTestCase(TestCase):

    def test_model_verbose_name(self):
        self.assertEqual(model_verbose_name(User), User._meta.verbose_name)

    def test_model_verbose_name_plural(self):
        self.assertEqual(model_verbose_name_plural(User), User._meta.verbose_name_plural)

    def test_model_name(self):
        self.assertEqual(model_name(User), User._meta.model_name)

    def test_app_label(self):
        self.assertEqual(app_label(User), User._meta.app_label)


class TestHasPermTestCase(TestCase):

    @staticmethod
    def _context(user):
        return {'request': SimpleNamespace(user=user)}

    def test_with_a_model_class_and_permission_granted(self):
        user = SimpleNamespace(is_authenticated=True, has_perm=lambda perm: perm == 'user.view_testuser')
        self.assertTrue(testhasperm(self._context(user), User, 'view'))

    def test_with_a_model_class_and_permission_denied(self):
        user = SimpleNamespace(is_authenticated=True, has_perm=lambda perm: perm == 'user.view_testuser')
        self.assertFalse(testhasperm(self._context(user), User, 'delete'))

    def test_with_an_app_label_dot_model_name_string(self):
        user = SimpleNamespace(is_authenticated=True, has_perm=lambda perm: perm == 'user.add_testuser')
        self.assertTrue(testhasperm(self._context(user), 'user.testuser', 'add'))

    def test_unauthenticated_user_never_has_permission(self):
        user = SimpleNamespace(is_authenticated=False, has_perm=lambda perm: True)
        self.assertFalse(testhasperm(self._context(user), User, 'view'))


class IfHasPermTagTestCase(TestCase):

    @staticmethod
    def _render(template_source, user):
        template = Template(template_source)
        context = Context({'request': SimpleNamespace(user=user), 'model': User})
        return template.render(context)

    def test_renders_the_ifhasperm_branch_when_permitted(self):
        source = (
            "{% load ajax_datatable_tags %}"
            "{% ifhasperm model 'view' %}YES{% else %}NO{% endifhasperm %}"
        )
        user = SimpleNamespace(is_authenticated=True, has_perm=lambda perm: True)
        self.assertEqual(self._render(source, user), 'YES')

    def test_renders_the_else_branch_when_denied(self):
        source = (
            "{% load ajax_datatable_tags %}"
            "{% ifhasperm model 'view' %}YES{% else %}NO{% endifhasperm %}"
        )
        user = SimpleNamespace(is_authenticated=False, has_perm=lambda perm: False)
        self.assertEqual(self._render(source, user), 'NO')

    def test_renders_empty_when_denied_and_there_is_no_else_branch(self):
        source = "{% load ajax_datatable_tags %}{% ifhasperm model 'view' %}YES{% endifhasperm %}"
        user = SimpleNamespace(is_authenticated=False, has_perm=lambda perm: False)
        self.assertEqual(self._render(source, user), '')

    def test_wrong_number_of_arguments_raises_template_syntax_error(self):
        source = "{% load ajax_datatable_tags %}{% ifhasperm model %}{% endifhasperm %}"
        with self.assertRaisesRegex(TemplateSyntaxError, 'takes three parameters'):
            Template(source)
