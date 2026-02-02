from .base import *

class TestLabelsSVG(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_svg_label_single(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            BotanicGarden.objects.get(name="Garden 1"),
            "pdf",
        )
        self.assert_pdf_size(response.content, [252, 102])

    def test_svg_label_multi_garden(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1"), BotanicGarden.objects.get(name="Garden 2")],
            "pdf",
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, [252, 102])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1")],
            "pdf",
        )
        self.assert_pdf_size(response.content, [252, 102])

    def test_svg_label_multi_individual(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="I1"),
            "individual",
            [Individual.objects.get(accession_number=1000), Individual.objects.get(accession_number=1001)],
            "pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, [252, 102])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="I1"),
            "individual",
            [Individual.objects.get(accession_number=1000)],
            "pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf_size(response.content, [252, 102])

    def test_svg_label_multi_specimen(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="S1"),
            "herbarium_specimen",
            [HerbariumSpecimen.objects.get(individual__accession_number=1002),
             HerbariumSpecimen.objects.get(individual__accession_number=1003)],
            "pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, [297, 212])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="S1"),
            "herbarium_specimen",
            [HerbariumSpecimen.objects.get(individual__accession_number=1002)],
            "pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf_size(response.content, [297, 212])

    def assert_zip_with_pdfs(self, response: HttpResponse, pdf_size: List[int]):
        fp = io.BytesIO(response.content)
        with zipfile.ZipFile(fp) as zf:
            self.assertEqual(2, len(zf.filelist))
            for fileinfo in zf.filelist:
                self.assertTrue(fileinfo.filename.endswith(".pdf"), fileinfo)
                with zf.open(fileinfo.filename) as fp:
                    self.assert_pdf_size(fp.read(), pdf_size)

    def assert_pdf_size(self, pdf_data: bytes, expected_size: List[int]):
        with tempfile.TemporaryDirectory() as path:
            filename = Path(path) / "label.pdf"
            filename.write_bytes(pdf_data)
            result = subprocess.check_output(["pdfinfo", str(filename)]).decode()
            match = re.match(r".*Page size:\s+(\d+\.?\d*)\sx\s(\d+.?\d*).*", result.replace("\n", " "))
            if not match:
                raise AssertionError(f"Page size not found in pdfinfo result: {result}")
            page_size = [int(float(g)) for g in match.groups()]
            self.assertEqual(list(expected_size), page_size, "PDF page size does not match")
