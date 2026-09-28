from .base import *

class TestLabelsSVG(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_svg_label_single(self):
        self.login(username="User1")

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            BotanicGarden.objects.get(name="Garden 1"),
            "pdf",
        )
        self.assert_pdf(response.content, expected_size_cm=[8.9, 3.6])

    def test_svg_label_multi_garden_pdf(self):
        self.login("User1")

        # --- multiple joined PDFs from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1"), BotanicGarden.objects.get(name="Garden 2")],
            "pdf",
        )
        self.assertEqual("application/pdf", response.headers["Content-Type"])
        self.assert_pdf(
            response.content,
            expected_size_cm=[8.9, 3.6],
            expected_pages=2,
        )

    def test_svg_label_multi_garden_zip(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1"), BotanicGarden.objects.get(name="Garden 2")],
            format="pdf",
            action_format_suffix="zip",
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, 2, [8.9, 3.6])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1")],
            "pdf",
            action_format_suffix="zip",
        )
        self.assert_pdf(response.content, expected_size_cm=[8.9, 3.6], expected_pages=1)


    def test_svg_label_multi_individual_pdf(self):
        self.login("User1")

        # --- multiple joined PDFs from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="I1"),
            "individual",
            [Individual.objects.get(accession_number=1000),
             Individual.objects.get(accession_number=1001),
             Individual.objects.get(accession_number=1002),
             ],
            "pdf",
            expect_unchecked_nomenclature=True,
        )
        self.assertEqual("application/pdf", response.headers["Content-Type"])
        self.assert_pdf(response.content, expected_size_cm=[8.9, 3.6], expected_pages=3)

    def test_svg_label_multi_individual_zip(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="I1"),
            "individual",
            [Individual.objects.get(accession_number=1000),
             Individual.objects.get(accession_number=1001),
             Individual.objects.get(accession_number=1002),
             ],
            "pdf",
            action_format_suffix="zip",
            expect_unchecked_nomenclature=True,
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, 3, [8.9, 3.6])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="I1"),
            "individual",
            [Individual.objects.get(accession_number=1000)],
            "pdf",
            action_format_suffix="zip",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf(response.content, expected_size_cm=[8.9, 3.6], expected_pages=1)

    def test_svg_label_multi_specimen_zip(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="S1"),
            "herbarium_specimen",
            [HerbariumSpecimen.objects.get(individual__accession_number=1002),
             HerbariumSpecimen.objects.get(individual__accession_number=1003)],
            "pdf",
            action_format_suffix="zip",
            expect_unchecked_nomenclature=True,
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, 2, [10.5, 7.5])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="S1"),
            "herbarium_specimen",
            [HerbariumSpecimen.objects.get(individual__accession_number=1002)],
            "pdf",
            action_format_suffix="zip",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf(response.content, expected_size_cm=[10.5, 7.5], expected_pages=1)

    def test_svg_label_multi_outplanting_zip(self):
        self.login("User1")

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="O2"),
            "outplanting",
            list(Outplanting.objects.all()),
            "pdf",
            action_format_suffix="zip",
            expect_unchecked_nomenclature=True,
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        self.assert_zip_with_pdfs(response, Outplanting.objects.all().count(), [8.9, 3.6])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="O2"),
            "outplanting",
            [Outplanting.objects.get(individual__accession_number=1000)],
            "pdf",
            action_format_suffix="zip",
            expect_unchecked_nomenclature=True,
        )
        self.assert_pdf(response.content, expected_size_cm=[8.9, 3.6], expected_pages=1)

    def assert_zip_with_pdfs(
            self,
            response: HttpResponse,
            expected_num_files: int,
            pdf_size_cm: List[float],
    ):
        fp = io.BytesIO(response.content)
        with zipfile.ZipFile(fp) as zf:
            self.assertEqual(expected_num_files, len(zf.filelist))
            for fileinfo in zf.filelist:
                self.assertTrue(fileinfo.filename.endswith(".pdf"), fileinfo)
                with zf.open(fileinfo.filename) as fp:
                    self.assert_pdf(fp.read(), expected_size_cm=pdf_size_cm, expected_pages=1)
