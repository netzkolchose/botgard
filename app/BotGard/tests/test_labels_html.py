import bs4

from .base import *

class TestLabelsHTML(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_html_label_single(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

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
        self.assert_pdf(response.content, num_pages=1)

        response = self.get_label_response(
            label_model, "individual", list(Individual.objects.all()), "html",
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
            label_model, "individual", individuals, "true_pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf(response.content, num_pages=3)

    def assert_pdf(self, content: bytes, num_pages: int):
        # check at least number of pages in PDF
        with tempfile.TemporaryDirectory() as path:
            filename = Path(path) / "label.pdf"
            filename.write_bytes(content)
            result = subprocess.check_output(["pdfinfo", str(filename)]).decode()
            match = re.match(r".*Pages:\s+(\d+).*", result.replace("\n", " "))
            if not match:
                raise AssertionError(f"'Pages' not found in pdfinfo result: {result}")
            self.assertEqual(num_pages, int(match.groups()[0]), f"Number of PDF pages does not match, got:\n{result}")

