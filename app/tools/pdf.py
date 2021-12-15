from django.http import HttpResponse


def create_pdf_response(filename):
    """
    Creates a HttpResponse object for delivering a PDF.
    The response will be a file attachment
    :param filename: The name of the file attachment
    :return: HttpResponse ready to be written to by reportlab
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response
