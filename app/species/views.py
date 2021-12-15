from django.template import loader
from species.models import Species
from django.db import connection
from django.http import HttpResponse

from individuals.models import *
from tools.permissions import *


@login_required
def is_available(request, forId):
    places = Outplanting.objects.filter(individual__species=forId).filter(plant_died=None)
    seeds = Individual.objects.filter(species=forId).filter(seed_available=True)

    t = loader.get_template('species/available.html')
    c = {
        'places': places,
        'seeds': seeds,
    }
    return HttpResponse(t.render(c))



# TODO: THIS IS ALL UNUSED/MEANINGLESS A.T.M

def distinct_query(table, fieldname, searchterm, limit):
    cursor = connection.cursor()
    querystring = "SELECT DISTINCT " + fieldname + " FROM " + table + " WHERE " + fieldname + ''' LIKE "''' + searchterm + '''%%" LIMIT ''' + str(
        limit)
    cursor.execute(querystring)
    row = cursor.fetchall()
    return row


# def ajax_autofillfamily(request):
# 	search_for=request.POST.get("genus")
# 	if (search_for==None):
# 		return HttpResponse(status=406)
# 	if (not search_for.isalnum()):
# 		return HttpResponse(status=403)
# 	else:
# 		#Species.objects.filter(genus=search_for)[0]
# 		return HttpResponse(str(Species.objects.filter(genus=search_for)[0].family), mimetype="text/plain")
#

@login_required
def ajax_name(request, forId):
    return HttpResponse(str(Species.objects.get(pk=forId)))


# def ajax_autofillauthor(request):
# 	search_for=request.POST.get("genus")
# 	if (search_for==None):
# 		return HttpResponse(status=406)
# 	if (not search_for.isalnum()):
# 		return HttpResponse(status=403)
# 	else:
# 		#Species.objects.filter(genus=search_for)[0]
# 		return HttpResponse(str(Species.objects.filter(genus=search_for)[0].genus_author), mimetype="text/plain")


@login_required
def ajax_autocomplete_individual_species(request, limit_by):
    search_for = request.POST.get('species_auto')
    if (search_for == None):
        return HttpResponse(status=406)  # return 406 if no post parameter

    search_for_splits = search_for.split(' ')
    search_genus = search_for_splits[0]

    if len(search_for_splits) > 1:
        search_species = search_for_splits[1]
        result_list = Species.objects.filter(family__genus__istartswith=search_genus).filter(
            species__istartswith=search_species)  # [:limit_by];
    else:
        result_list = Species.objects.filter(family__genus__istartswith=search_genus)  # [:limit_by];

    return_value = ''
    if len(result_list) > 0:  # check if there are any results
        for elem in result_list:
            return_value += '<li title="' + str(elem.pk) + '">' + str(elem) + '</li>'
        return HttpResponse('<ul>' + return_value + '</ul>')
    else:
        return HttpResponse(status=204)  # return no content code if no results


@login_required
def ajax_autocomplete_species(request, search_item, limit_by):
    search_for = request.POST.get(search_item)

    whitelist = (
        'species', 'species_author', 'subspecies', 'subspecies_author', 'variety', 'variety_author', 'form',
        'form_author',
        'cultivar')  # contains allowed search fields to prevent code injection
    if (search_for == None):
        return HttpResponse(status=406)  # return 406 if no post parameter

    blacklist = '''@;'"'''  # blacklisted characters
    for elem in blacklist:
        if elem in search_for:
            return HttpResponse('<ul><li style="background-color:#ff9a89">Zeichen erlaubt kein Autocomplete</li></ul>')
            # 	return HttpResponse(repr(blacklist))

    # Do some tesings for security, check wether search_item is in the whitelist, the searchterm consists of alphanums
    if search_item in whitelist:
        result_list = distinct_query("species_species", search_item, search_for, limit_by)
        return_value = ''
        if len(result_list) > 0:  # check if there are any results
            for elem in result_list:
                return_value += '<li>' + elem[0] + '</li>'
            return HttpResponse('<ul>' + return_value + '</ul>')
        else:
            return HttpResponse(status=204)  # return no content code if no results
    else:
        return HttpResponse(status=403)  # return forbidden if security tests failed


@login_required
def ajax_autocomplete_families(request, search_item, limit_by):
    search_for = request.POST.get(search_item)

    whitelist = ('genus', 'genus_author', 'family', 'subfamily', 'tribus',
                 'subtribus')  # contains allowed search fields to prevent code injection
    if (search_for == None):
        return HttpResponse(status=406)  # return 406 if no post parameter

    blacklist = '''@;'"'''  # blacklisted characters
    for elem in blacklist:
        if elem in search_for:
            return HttpResponse('<ul><li style="background-color:#ff9a89">Zeichen erlaubt kein Autocomplete</li></ul>')

    if (
                search_item in whitelist):  # Do some tesings for security, check wether search_item is in the whitelist, the searchterm consists of alphanums
        result_list = distinct_query("species_family", search_item, search_for, limit_by)
        return_value = ''
        if len(result_list) > 0:  # check if there are any results
            for elem in result_list:
                return_value += '<li>' + elem[0] + '</li>'
            return HttpResponse('<ul>' + return_value + '</ul>')
        else:
            return HttpResponse(status=204)  # return no content code if no results
    else:
        return HttpResponse(status=403)  # return forbidden if security tests failed
