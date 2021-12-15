from modeltranslation.translator import translator, TranslationOptions
from .models import (KeyValue)


class KeyValueTranslationOptions(TranslationOptions):
    fields = ('value',)
    empty_values = {'language': None}


translator.register(KeyValue, KeyValueTranslationOptions)
