from unittest import mock
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from wagtail.admin.filters import FilteredModelChoiceField, WagtailFilterSet
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils

User = get_user_model()


class TestFilteredModelChoiceField(WagtailTestUtils, TestCase):
    def setUp(self):
        self.musicians = Group.objects.create(name="Musicians")
        self.actors = Group.objects.create(name="Actors")

        self.david = self.create_user(
            "david",
            "david@example.com",
            "kn1ghtr1der",
            first_name="David",
            last_name="Hasselhoff",
        )
        self.david.groups.set([self.musicians, self.actors])

        self.kevin = self.create_user(
            "kevin",
            "kevin@example.com",
            "6degrees",
            first_name="Kevin",
            last_name="Bacon",
        )
        self.kevin.groups.set([self.actors])

        self.morten = self.create_user(
            "morten",
            "morten@example.com",
            "t4ke0nm3",
            first_name="Morten",
            last_name="Harket",
        )
        self.morten.groups.set([self.musicians])

    def test_with_relation(self):
        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by(User.USERNAME_FIELD),
                filter_field="id_group",
                filter_accessor="groups",
            )

        form = UserForm()
        html = str(form["users"])
        expected_html = """
            <select name="users" data-widget="filtered-select" data-filter-field="id_group" required id="id_users">
                <option value="" selected>---------</option>
                <option value="{david}" data-filter-value="{musicians},{actors}">{david_username}</option>
                <option value="{kevin}" data-filter-value="{actors}">{kevin_username}</option>
                <option value="{morten}" data-filter-value="{musicians}">{morten_username}</option>
            </select>
        """.format(
            david=self.david.pk,
            kevin=self.kevin.pk,
            morten=self.morten.pk,
            musicians=self.musicians.pk,
            actors=self.actors.pk,
            david_username=self.david.get_username(),
            kevin_username=self.kevin.get_username(),
            morten_username=self.morten.get_username(),
        )
        self.assertHTMLEqual(html, expected_html)

    def test_with_callable(self):
        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by(User.USERNAME_FIELD),
                filter_field="id_group",
                filter_accessor=lambda user: user.groups.all().order_by("name"),
            )

        form = UserForm()
        html = str(form["users"])
        expected_html = """
            <select name="users" data-widget="filtered-select" data-filter-field="id_group" required id="id_users">
                <option value="" selected>---------</option>
                <option value="{david}" data-filter-value="{actors},{musicians}">{david_username}</option>
                <option value="{kevin}" data-filter-value="{actors}">{kevin_username}</option>
                <option value="{morten}" data-filter-value="{musicians}">{morten_username}</option>
            </select>
        """.format(
            david=self.david.pk,
            kevin=self.kevin.pk,
            morten=self.morten.pk,
            musicians=self.musicians.pk,
            actors=self.actors.pk,
            david_username=self.david.get_username(),
            kevin_username=self.kevin.get_username(),
            morten_username=self.morten.get_username(),
        )
        self.assertHTMLEqual(html, expected_html)


class TestWagtailFilterSetAddLocaleFilter(WagtailTestUtils, TestCase):
    def test_model_none_does_not_add_filter(self):
        class TestFilterSet(WagtailFilterSet):
            class Meta:
                model = None
                fields = []

        with override_settings(WAGTAIL_I18N_ENABLED=True):
            filterset = TestFilterSet()
        
        self.assertNotIn("locale", filterset.filters)

    def test_model_not_translatable_does_not_add_filter(self):
        
        class TestFilterSet(WagtailFilterSet):
            class Meta:
                model = User
                fields = []

        with override_settings(WAGTAIL_I18N_ENABLED=True):
            filterset = TestFilterSet()
        
        self.assertNotIn("locale", filterset.filters)

    @override_settings(
        WAGTAIL_I18N_ENABLED=True,
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("pt", "Portuguese"),
        ],
    )
    def test_locale_filter_already_exists_not_overwritten(self):
        from wagtail.admin.filters import LocaleFilter
        from wagtail.models import Locale
        
        Locale.objects.get_or_create(language_code="en")
        Locale.objects.get_or_create(language_code="pt")
        
        class TestFilterSet(WagtailFilterSet):
            locale = LocaleFilter(label="Custom Label")
            
            class Meta:
                model = Page
                fields = ["locale"]

        filterset = TestFilterSet()
        
        # Verificar que mantém o filtro customizado
        self.assertIn("locale", filterset.filters)
        self.assertEqual(filterset.filters["locale"].label, "Custom Label")

    @override_settings(
        WAGTAIL_I18N_ENABLED=True,
        WAGTAIL_CONTENT_LANGUAGES=[("en", "English")],
    )
    def test_single_language_does_not_add_filter(self):
        from wagtail.models import Locale
        
        Locale.objects.get_or_create(language_code="en")
        
        class TestFilterSet(WagtailFilterSet):
            class Meta:
                model = Page
                fields = []

        filterset = TestFilterSet()

        self.assertNotIn("locale", filterset.filters)

    @override_settings(
        WAGTAIL_I18N_ENABLED=True,
        WAGTAIL_CONTENT_LANGUAGES=[],
    )
    def test_no_languages_does_not_add_filter(self):
        class TestFilterSet(WagtailFilterSet):
            class Meta:
                model = Page
                fields = []

        filterset = TestFilterSet()
        
        self.assertNotIn("locale", filterset.filters)

    @override_settings(
        WAGTAIL_I18N_ENABLED=True,
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("pt", "Portuguese"),
            ("fr", "French"),
        ],
    )
    def test_multiple_languages_adds_locale_filter(self):
        from wagtail.admin.filters import LocaleFilter
        from wagtail.models import Locale
        
        Locale.objects.get_or_create(language_code="en")
        Locale.objects.get_or_create(language_code="pt")
        Locale.objects.get_or_create(language_code="fr")
        
        class TestFilterSet(WagtailFilterSet):
            class Meta:
                model = Page
                fields = []

        filterset = TestFilterSet()
        
        self.assertIn("locale", filterset.filters)
        self.assertIsInstance(filterset.filters["locale"], LocaleFilter)
        
        choices = filterset.filters["locale"].extra["choices"]
        self.assertGreaterEqual(len(choices), 2)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_i18n_disabled_does_not_call_method(self):
        from wagtail.models import Locale
        
        Locale.objects.get_or_create(language_code="en")
        Locale.objects.get_or_create(language_code="pt")
        
        class TestFilterSet(WagtailFilterSet):
            class Meta:
                model = Page
                fields = []

        filterset = TestFilterSet()

        self.assertNotIn("locale", filterset.filters)
