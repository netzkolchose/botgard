import re

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex

from botman.models import BotanicGarden
from species.models import Family, Species
from individuals.models import Department, Territory, Individual, Outplanting
from labels.models import LabelDefinition
from tickets.models import BasicTicket, LaserGravurTicket

from .fixtures import create_test_fixtures


class TestAllViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def assertStatus(self, expected_status: int, response, text: str):
        if getattr(response, "url", None):
            text = text + f" / redirect: {response.url}"
        if getattr(response, "redirect_chain", None):
            text = text + f" / redirect_chain: {response.redirect_chain}"
        self.assertEqual(expected_status, response.status_code, text)

    def get_all_urls(self):
        """
        Returns ALL urls in this project

        :return: list of 2-tuples
            1. url-name as usable in django.urls.reverse()
            2. list of url parameter names
        """
        from django_extensions.management.commands.show_urls import Command as ShowUrlsCommand
        from BotGard.urls import urlpatterns

        cmd = ShowUrlsCommand()

        urls = []
        for (func, regex, url_name) in cmd.extract_views_from_urlpatterns(urlpatterns):
            url = simplify_regex(regex)
            params = re.findall(r"<([^>]+)>", url)
            urls.append((url_name, params))
        return urls

    def test_model_views(self):
        """
        Call each model's admin:change page
        """
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        for Model in [
            BotanicGarden, Family, Species,
            Territory, Department, Individual,
            LabelDefinition,
            # Outplanting (is not visible in admin)
        ]:
            pks = Model.objects.all().order_by("pk").values_list("pk", flat=True)
            self.assertGreaterEqual(pks.count(), 2, f"Not enough {Model.__name__} in db-fixtures")

            for pk in pks:
                app_name, model_name = Model._meta.label_lower.split(".")
                url_name = f"admin:{app_name}_{model_name}_change"
                url = reverse(url_name, args=(pk, ))

                response = self.client.get(url, follow=False)
                self.assertStatus(200, response, f"in {url_name} {url}")

    def test_GET_no_params(self):
        """
        HTTP GET on all URLs that do not require url-parameters
        """
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        for url_name, url_params in self.get_all_urls():
            if url_params:
                continue
            if url_name in ("admin:login", "admin:logout", "admin:autocomplete"):
                continue

            # TODO: permission not working somehow
            if url_name in (
                    "botman:data_admin", "botman:activity", "index",
                    "labels:doc_template", "sidebar:add_bookmark",
                    "sidebar:update_bookmark_order", "sidebar:new_note",
                    "ajax:model_json", "ajax:choices_json",
            ):
                continue

            try:
                url = reverse(url_name)
                print("testing", url_name, url)
                response = self.client.get(url)

                expected_status = 200
                if url_name in (
                    "botman:index",
                ):
                    expected_status = 302

                self.assertStatus(expected_status, response, f"in {url_name} {url}")

            except Exception as e:
                print(f"ERROR IN VIEW {url_name}: {type(e).__name__}: {e}")
                raise

    def test_GET_params_no_admin(self):
        """
        HTTP GET against all views than require url parameters.

        PARAM_MAPPING is a dict with key
            url-name (that can be used with django.urls.reverse)
        and value of tuple:
            1. entry: List of query-sets for each url-parameter
            2. entry: optional list of query parameter strings
        """
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        PARAM_MAPPING = {
            "individuals:checklist_territory": (
                [Territory.objects.all()],
            ),
            "individuals:checklist_department": (
                [Department.objects.all()],
            ),
            "species:is_available": (
                [Species.objects.all()],
            ),
            #"seedcatalog:edit_seeds": ['forId'],
            #"seedcatalog:add_seed": ['seedId', 'catalogId'],
            #"seedcatalog:add_seed_to_current": ['seedId'],
            #"seedcatalog:remove_seed": ['seedId', 'catalogId'],
            #"seedcatalog:generate": ['catalogId'],
            #"seedcatalog:debug": ['catalogId'],
            #"seedcatalog:duplicate_catalog": ['catalogId'],
            #"seedcatalog:finalize_catalog": ['catalogId'],
            "tickets:state": (
                [BasicTicket.objects.all()],
            ),
            "tickets:show_ticket": (
                [BasicTicket.objects.all()],
            ),
            #"tickets:set_label_done": ['etikett_individual_pk'],
            "labels:individual": (
                [LabelDefinition.objects.filter(type="individual"), Individual.objects.all()],
                ["", "format=pdf", "format=png", "format=html&include_links=1"],
            ),
            "labels:garden": (
                [LabelDefinition.objects.filter(type="garden"), BotanicGarden.objects.all()],
                ["", "format=pdf", "format=png", "format=html&include_links=1"],
            ),
            "labels:random": (
                [LabelDefinition.objects.all()],
                ["", "format=pdf", "format=png", "format=html&include_links=1"],
            ),
            "labels:random_individual": (
                [LabelDefinition.objects.filter(type="individual")],
            ),
            "labels:random_garden": (
                [LabelDefinition.objects.filter(type="garden")],
            )
            #"sidebar:delete_bookmark": ['id'],
            #"sidebar:delete_note": ['id'],
            #"sidebar:publish_note": ['id', 'publish'],
            #"sidebar:edit_note": ['id'],
        }
        for url_name, url_params in self.get_all_urls():
            if not url_name or url_name.startswith("admin:") or not url_params:
                continue

            if url_name not in PARAM_MAPPING:
                # TODO: need to add all current and then raise if a new view comes along
                #print(url_name, url_params)
                continue

            param_qsets = PARAM_MAPPING[url_name][0]
            if len(param_qsets) == 1:
                params = [
                    (pk,)
                    for pk in param_qsets[0].order_by("pk").values_list("pk", flat=True)
                ]
            elif len(param_qsets) == 2:
                params = [
                    (pk1, pk2)
                    for pk1 in param_qsets[0].order_by("pk").values_list("pk", flat=True)
                    for pk2 in param_qsets[1].order_by("pk").values_list("pk", flat=True)
                ]
            else:
                raise ValueError(f"Can not handle param-length {len(param_qsets)}")

            query_args = [""]
            if len(PARAM_MAPPING[url_name]) > 1:
                query_args = PARAM_MAPPING[url_name][1]

            for query_arg in query_args:
                for args in params:

                    url = reverse(url_name, args=args)
                    if query_arg:
                        url += "?" + query_arg
                    print("testing", url_name, url)

                    try:
                        response = self.client.get(url)
                        self.assertStatus(200, response, f"in {url_name} {url}")
                    except Exception as e:
                        print(f"ERROR IN VIEW {url_name}: {type(e).__name__}: {e}")
                        raise

