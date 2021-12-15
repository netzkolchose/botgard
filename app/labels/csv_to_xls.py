import xlwt
import csv
from io import BytesIO
from typing import Union

from django.utils.translation import gettext_lazy as _


def convert_csv_to_xls(csv_markup_or_rows: Union[str, list]) -> bytes:
    book = xlwt.Workbook(encoding="utf-8")
    sheet = book.add_sheet(str(_("sheet 1")))

    if isinstance(csv_markup_or_rows, str):
        csv_reader = csv.reader(csv_markup_or_rows.splitlines())
        rows = list(csv_reader)
    elif isinstance(csv_markup_or_rows, list):
        rows = csv_markup_or_rows
    else:
        raise TypeError(f"Expected str or list, got '{type(csv_markup_or_rows)}'")

    for y, row in enumerate(rows):
        for x, val in enumerate(row):
            sheet.write(y, x, val)

    stream = BytesIO()
    book.save(stream)
    stream.seek(0)
    return stream.read()
