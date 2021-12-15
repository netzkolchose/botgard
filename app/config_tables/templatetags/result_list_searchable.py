from django.template import Library

register = Library()

from django.contrib.admin.templatetags.admin_list import result_list


@register.inclusion_tag("config_tables/change_list_results_searchable.html")
def result_list_searchable(cl, change_list_searchable_headers, django_hidden_fields):
    """
    Displays the headers, searchbar and data list together
    """
    context = result_list(cl)
    context.update({
        'change_list_searchable_headers': change_list_searchable_headers,
        'django_hidden_fields': django_hidden_fields,
    })
    return context
