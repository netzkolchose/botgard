from django.template import Library

register = Library()

from django.contrib.admin.templatetags.admin_list import result_list
import config_app


@register.inclusion_tag("config_tables/change_list_results_searchable.html")
def result_list_searchable(cl, change_list_searchable_headers, django_hidden_fields):
    """
    Displays the headers, searchbar and data list together
    """
    table_class = None
    table_height = None
    sticky = config_app.get_value("sticky_table_headers")
    if sticky.get("sticky"):
        table_class = "sticky-header"
        if h := sticky.get("height"):
            table_height = h

    context = result_list(cl)
    context.update({
        'change_list_searchable_headers': change_list_searchable_headers,
        'django_hidden_fields': django_hidden_fields,
        'html_table_class': table_class,
        'html_table_height': table_height,
    })
    return context
