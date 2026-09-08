from django.forms import widgets


class SpeciesAuditWidget(widgets.Input):
    template_name = "individuals/species_audit_widget.html"

    def format_value(self, value):
        if value:
            value = [
                {
                    **row,
                    "user": row["user"] or "-",
                    "date": row["date"] or "-",
                    "literature": row["literature"] or "-",
                }
                for row in value
            ]
        return value
