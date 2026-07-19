from .models import *
from .fields import *


def CustomPropertiesModelMixin(related_name_model: str):
    class _CustomPropertiesModel(models.Model):
        class Meta:
            abstract = True

        custom_values_bool = CustomPropertyValuesBoolField(related_name=f"{related_name_model}_values_bool")
        custom_values_text = CustomPropertyValuesTextField(related_name=f"{related_name_model}_values_text")

        def __getattr__(self, item):
            if not (isinstance(item, str) and item.startswith("custom_property_")):
                return super().__getattribute__(item)

            pk = item[16:]
            print("X", repr(pk))
            try:
                prop = (
                    self.custom_values_bool.filter(property__pk=pk).first()
                    or self.custom_values_text.filter(property__pk=pk).first()
                )
                return prop.value
            except:
                raise AttributeError(f"CustomProperty missing: {item}")


    return _CustomPropertiesModel