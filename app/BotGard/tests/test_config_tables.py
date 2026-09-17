import django.contrib.admin
import django.apps

from .base import *
from config_tables.admin import ConfigurableTable


class TestConfigTables(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def setUp(self):
        self.login(username="User1"),

    def test_config_table_garden(self):
        cl = self.get_changelist("botman", "botanicgarden")
        cl.assert_columns([
            'change_link_decorator', 'name', 'code', 'phone',
            'website_link_decorator', 'email_link_decorator',
            'label_link_decorator', 'delete_link_decorator',
        ])

        cl.set_columns([
            'address', 'change_link_decorator',
            'full_name_generated', 'catalog_date_generated',
            'num_orders_generated',
        ])


    def test_config_table_individual(self):
        cl = self.get_changelist("individuals", "individual")
        cl.assert_columns([
            'change_link_decorator', 'accession_number', 'accession_extension',
            'ipen_generated', 'species_link_decorator', 'departments_decorator',
            'is_alive', 'source', 'etikett_link_decorator'
        ])

        cl.set_columns([
            'image_decorator', 'change_link_decorator',
            'delete_link_decorator', 'etikett_detail_decorator',
            'territories_decorator',
        ])

    @override_settings(DEBUG=True)
    def test_all_filter_columns(self):
        """
        Enable all possible columns for each changelist and used them for filtering.
        Makes sure that all foreign relation filters are configured in ModelAdmin.list_filer
        (via ForeignKeyFilter)
        """
        all_changelist_names = []
        for url in django.contrib.admin.site.get_urls():
            if hasattr(url, "urlconf_name"):
                for n in url.urlconf_name:
                    if n.name and n.name.endswith("_changelist"):
                        if not n.name.startswith("config_tables") and not n.name.startswith("config_app"):
                            all_changelist_names.append(n.name)

        num_checked_changelists = 0
        for changelist_name in all_changelist_names:
            with self.subTest(changelist_name):
                app_name, model_name, _ = changelist_name.split("_")
                if app_name == "auth":
                    continue

                cl = self.get_changelist(app_name, model_name)
                if not cl.is_configurable_table():
                    continue
                num_checked_changelists += 1

                columns = cl.get_all_possible_columns()

                # change table-settings to include all columns
                cl.set_columns(columns)

                # load changelist and get all column filters
                response = self.client.get(reverse(f"admin:{changelist_name}"))
                soup = self.get_soup(response.content)

                column_filters = []
                for elem in soup.find_all("input", {"class": "filter-form-element"}):
                    column_filters.append(elem.attrs["name"])

                query_string = "&".join(
                    f"{key}=x" for key in column_filters
                )
                response = self.client.get(reverse(f"admin:{changelist_name}") + "?" + query_string)

                if response.status_code == 302:
                    raise AssertionError(f"{changelist_name} redirected to {response.headers['location']}")

                if response.status_code != 200:
                    raise AssertionError(f"{changelist_name} responded with {response.status_code}\n{self.get_response_error(response)}")

        self.assertGreaterEqual(num_checked_changelists, 18)
