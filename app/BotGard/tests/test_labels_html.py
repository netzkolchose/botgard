import bs4

from .base import *

class TestLabelsHTML(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_html_label_individual_single(self):
        self.login(username="User1")

        label_model = LabelDefinition.objects.get(id_name="I2")

        # single label HTML
        response = self.get_label_response(label_model, "individual", Individual.objects.get(accession_number=1000), "html")
        # print(response.content)
        self.assertIn(b"""<div class="page-break">IPEN: AU-0-GARD1-1000</div>""", response.content)  # has object markup
        self.assertIn(b"""<!DOCTYPE html>""", response.content)  # has page markup

        # single label PDF
        response = self.get_label_response(
            label_model, "individual", Individual.objects.get(accession_number=1000), "pdf",
        )
        #print(response.content)
        self.assert_pdf(response.content, expected_size_cm=[21., 27.], expected_pages=1)

    def test_html_label_individual_multi(self):
        self.login(username="User1")

        label_model = LabelDefinition.objects.get(id_name="I2")

        response = self.get_label_response(
            label_model, "individual", list(Individual.objects.all()), "html", action_format_suffix="html",
            expect_unchecked_nomenclature=True,
        )

        self.assertIn(b"""<div class="page-break">IPEN: AU-0-GARD1-1000</div>""", response.content)  # has object markup
        self.assertIn(b"""<div class="page-break">IPEN: IT-0-GARD2-1001</div>""", response.content)
        self.assertIn(b"""<div class="page-break">IPEN: CZ-0-GARD1-1002</div>""", response.content)
        self.assertIn(b"""<div class="page-break">IPEN: ES-0-GARD2-1003</div>""", response.content)
        self.assertIn(b"""<!DOCTYPE html>""", response.content)

        individuals = list(Individual.objects.all())[:3]
        self.assertEqual(3, len(individuals))
        response = self.get_label_response(
            label_model, "individual", individuals, "pdf", action_format_suffix="pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf(response.content, expected_size_cm=[21., 27.], expected_pages=3)
