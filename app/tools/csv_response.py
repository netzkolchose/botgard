import csv

from django.http import HttpResponse


def csv_response(filename, headers, rows):

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    csv_writer = csv.writer(
        response,
        delimiter=",",
        doublequote='"',
        escapechar='\\',
        lineterminator='\n',
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    )

    csv_writer.writerow(headers)
    csv_writer.writerows(rows)

    return response

