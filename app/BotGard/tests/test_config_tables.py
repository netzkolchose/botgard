import inspect
import importlib
import os.path

import django.contrib.admin
import django.apps

from .base import *
from config_tables.admin import ConfigurableTable


class TestConfigTables(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def setUp(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

    def test_config_table_garden(self):
        self.assert_changelist_columns("botman", "botanicgarden", [
            'change_link_decorator', 'name', 'code', 'phone',
            'website_link_decorator', 'email_link_decorator',
            'label_link_decorator', 'delete_link_decorator',
        ])

        prop_garden = CustomProperty.objects.get(name="garden_important")
        prop_species = CustomProperty.objects.get(name="poisonous")
        self.assert_change_changelist_columns("botman", "botanicgarden", [
            'address', 'change_link_decorator',
            'full_name_generated', 'catalog_date_generated',
            'num_orders_generated',
            f'custom_property_decorator_{prop_garden.pk}',
            f'custom_property_decorator_{prop_species.pk}',
        ], not_in_new_columns=[
            f'custom_property_decorator_{prop_species.pk}',
        ])

    def test_config_table_species(self):
        self.assert_changelist_columns("species", "species", [
            'change_link_decorator',
            'genus_single', 'family_single',
            'species', 'deutscher_name', 'synonyme',
            'area_of_distribution_etikettxt',
            'search_individuals_link_decorator', 'search_seeds_link_decorator', 'availability_decorator',
            'alive_individuals_decorator',
            'delete_link_decorator',
        ])

        prop_garden = CustomProperty.objects.get(name="garden_important")
        prop_species = CustomProperty.objects.get(name="poisonous")
        self.assert_change_changelist_columns("species", "species", [
            'species',
            'genus_single',
            'synonyme',
            'deutscher_name',
            'area_of_distribution_etikettxt',
            f'custom_property_decorator_{prop_species.pk}',
        ], not_in_new_columns=[
            f'custom_property_decorator_{prop_garden.pk}',
        ])

    def test_config_table_individual(self):
        self.assert_changelist_columns("individuals", "individual", [
            'change_link_decorator', 'accession_number', 'accession_extension',
            'ipen_generated', 'species_link_decorator', 'departments_decorator',
            'is_alive', 'source', 'etikett_link_decorator'
        ])

        prop = CustomProperty.objects.get(name="individual_comment")
        self.assert_change_changelist_columns("individuals", "individual", [
            'image_decorator', 'change_link_decorator',
            'delete_link_decorator', 'etikett_detail_decorator',
            'territories_decorator',
            f'custom_property_decorator_{prop.pk}',
        ])

    @override_settings(DEBUG=True)
    def test_all_filter_columns(self):
        all_changelist_names = []
        for url in django.contrib.admin.site.get_urls():
            if hasattr(url, "urlconf_name"):
                for n in url.urlconf_name:
                    if n.name and n.name.endswith("_changelist"):
                        if not n.name.startswith("config_tables") and not n.name.startswith("config_app"):
                            all_changelist_names.append(n.name)

        class FakeRequest:
            user = User.objects.get(username="User1")
        fake_request = FakeRequest()

        num_custom_props_tested = 0

        for changelist_name in all_changelist_names:
            with self.subTest(changelist_name):
                app_name, model_name, _ = changelist_name.split("_")

                Model = django.apps.apps.get_model(app_name, model_name)
                admin: django.contrib.admin.ModelAdmin = django.contrib.admin.site.get_model_admin(Model)
                if not isinstance(admin, ConfigurableTable):
                    continue

                # fetch all available columns of the model
                columns = admin.get_modelattributes_treepart(Model)
                columns += admin.get_decorated_functions(Model)
                columns = admin.apply_blacklist(columns)
                columns = [c[1] for c in columns]
                # change table-settings to include all columns
                self.assert_change_changelist_columns(app_name, model_name, columns)

                # load changelist and get all column filters
                response = self.client.get(reverse(f"admin:{changelist_name}"))
                soup = self.get_soup(response.content)

                column_filters = []
                for elem in itertools.chain(
                        soup.find_all("input", {"class": "filter-form-element"}),
                        soup.find_all("select", {"class": "filter-form-element"}),
                ):
                    column_filters.append(elem.attrs["name"])

                for props in fixtures.CUSTOM_PROPERTIES:
                    if model_name == props["model"].split(".")[-1].lower():
                        num_custom_props_tested += 1
                        prop = CustomProperty.objects.get(name=props["name"])
                        self.assertIn(f"custom_property_{prop.pk}", column_filters)
                        break

                query_string = "&".join(
                    f"{key}=1" for key in column_filters
                )
                response = self.client.get(reverse(f"admin:{changelist_name}") + "?" + query_string)

                if response.status_code == 302:
                    raise AssertionError(
                        f"{changelist_name} redirected to {response.headers['location']}"
                        f"\nquery_string={query_string}"
                    )

                if response.status_code != 200:
                    raise AssertionError(f"{changelist_name} responded with {response.status_code}\n{self.get_response_error(response)}")

        self.assertEqual(len(fixtures.CUSTOM_PROPERTIES), num_custom_props_tested)

    def test_creation_fields_filterable(self):
        """
        Check that all models with `creation_fields=True` have the
        users fields in `ModelAdmin.list_filter`
        """
        problems = {
            "not based on config_tables.admin.ConfigurableTable": [],
            "missing 'created_by'/'modified_by' in ModelAdmin.list_filter": [],
        }
        for model_class, model_admin in self.get_model_admins():
            if getattr(model_class, "_has_creation_fields", None):
                if not isinstance(model_admin, ConfigurableTable):
                    problems["not based on config_tables.admin.ConfigurableTable"].append(model_admin)
                found = 0
                for f in model_admin.list_filter:
                    if isinstance(f, (list, tuple)):
                        if isinstance(f[0], str):
                            if f[0].startswith("created_by__"):
                                found += 1
                            elif f[0].startswith("modified_by__"):
                                found += 1
                if found < 2:
                    problems["missing 'created_by'/'modified_by' in ModelAdmin.list_filter"].append(model_admin)

        msg = io.StringIO()
        for key, admins in problems.items():
            if admins:
                print(f"\n{key}:\n", file=msg)
                for admin in admins:
                    print(f"  {admin}", file=msg)
        msg.seek(0)
        msg = msg.read()

        if msg:
            raise AssertionError(f"For BotGardBaseModel(creation_fields=True):\n{msg}")
