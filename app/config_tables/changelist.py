from functools import reduce
from operator import or_
from typing import Optional, Type

from django.db import models
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.utils import get_fields_from_path, NotRelationField
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.exceptions import (
    FieldDoesNotExist,
    ImproperlyConfigured,
    SuspiciousOperation,

)

from tools.search_fields import make_filter_term_compatible_with_natural_sort


class ConfigurableChangeList(ChangeList):

    def get_queryset(self, request, exclude_parameters=None):
        """
        Copied from django.contrib.admins.views.main.ChangeList

        Supports filter specialities.
        Only replaces the `build_q_object_from_lookup_parameters` call!
        """
        # First, we collect all the declared list filters.
        (
            self.filter_specs,
            self.has_filters,
            remaining_lookup_params,
            filters_may_have_duplicates,
            self.has_active_filters,
        ) = self.get_filters(request)
        # Then, we let every list filter modify the queryset to its liking.
        qs = self.root_queryset
        for filter_spec in self.filter_specs:
            if (
                    exclude_parameters is None
                    or filter_spec.expected_parameters() != exclude_parameters
            ):
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs

        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            q_object = self._build_q_object_from_lookup_parameters(remaining_lookup_params)
            qs = qs.filter(q_object)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        if not qs.query.select_related:
            qs = self.apply_select_related(qs)

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_may_have_duplicates = self.model_admin.get_search_results(
            request,
            qs,
            self.query,
        )

        # Set query string for clearing all filters.
        self.clear_all_filters_qs = self.get_query_string(
            new_params=remaining_lookup_params,
            remove=self.get_filters_params(),
        )
        # Remove duplicates from results, if necessary
        if filters_may_have_duplicates | search_may_have_duplicates:
            return qs.distinct()
        else:
            return qs

    def _build_q_object_from_lookup_parameters(self, parameters: dict):
        q_object = models.Q()
        for param, param_item_list in parameters.items():

            # make filter terms compatible with `natural_sort` collation
            if param.split("__")[-1] in ("icontains", "istartswith"):
                if field := self._get_model_field(param):
                    if getattr(field, "db_collation", None) == "natural_sort":
                        param_item_list = [
                            make_filter_term_compatible_with_natural_sort(item)
                            for item in param_item_list
                        ]

            q_object &= reduce(or_, (models.Q((param, item)) for item in param_item_list))
        return q_object

    def _get_model_field(self, filter_param: str) -> Optional[models.Field]:
        """
        Get the model field from filter parameter, including related model fields.
        Recursively removes final __lookup until field is found
        """
        parts = filter_param.split("__")
        while parts:
            try:
                fields = get_fields_from_path(self.model, "__".join(parts))
            except NotRelationField:
                parts = parts[:-1]
                continue

            return fields[-1]
