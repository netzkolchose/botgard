# Django filters, needed when creating LaTeX files with the django template language

from django.template.defaultfilters import stringfilter
from django.template import Library


register = Library()


@register.filter
@stringfilter
def brackets(value):
    """
    surrounds the value with { }
    You have to use this filter whenever you would need something like
    {{{ field }}} in a template.
    """
    return "{%s}" % value
 
 
REPLACEMENTS = {
    "§": "\\textsection{}",
    "$": "\\textdollar{}",
    "LaTeX": "\\LaTeX \\ ",
    " TeX": " \\TeX \\ ",
    "€": "\\euro",
    "°": "\\textdegree ",
    }
 
ESCAPES = ("&", "{", "}", "%", "_",)


@register.filter
@stringfilter
def texify(value):
    """
    escapes/replaces special character with appropriate latex commands
    """
    tex_value = []
    # escape special symbols
    for char in value:
        if char in ESCAPES:
            tex_value.append("%s" % ("\\%s" % char))
        else:
            tex_value.append(char)
    
    tex_value = "".join(tex_value)
    # replace symbols / words with latex commands
    for key, value in REPLACEMENTS.items():
        tex_value = tex_value.replace(key, value)
    
    return "%s" % tex_value


@register.filter
def tex_full_name(species):
    word_list = species.full_name_each_author_list()
    ret_list = []
    for word in word_list:
        if word.get("author"):
            word = "{\it %s }" % texify(word["author"])
        else:
            word = texify(word["name"])
        ret_list.append(word)

    return " ".join(ret_list)

