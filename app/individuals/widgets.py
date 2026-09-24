from django.forms import widgets


class SpeciesAuditWidget(widgets.Input):
    template_name = "individuals/species_audit_widget.html"

    def format_value(self, value):
        if value:
            value = [
                {
                    **row,
                    "user": row.get("user") or "-",
                    "date": row.get("date") or "-",
                    "literature": row.get("literature") or "-",
                    "comment": row.get("comment") or "-",
                }
                for row in value
            ]
        return value
