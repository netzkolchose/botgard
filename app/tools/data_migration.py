from django.db import transaction, IntegrityError
from django.db.models import CharField

from botman.models import BotanicGarden
from species.models import Species, Family
from individuals.models import Individual, Seed, Outplanting, Territory, Department
from species.models import Species, Family
from tickets.models import LaserGravurTicket

"""

Please add ALL dependencies here so we can arrange for re-generating the 
fields on changes to their source

    botman:
        BotanicGarden.full_name_generated -> self
       
    individuals:
        Territory.name_generated -> self
        Territory.num_xxx -> Outplanting
        
        Department.num_xxx -> Outplanting
        Department.full_code -> self, Territory.code
        
        Outplanting.department -> Department
        
        Individual.ipen_generated -> self
        Individual.is_alive_generated -> [Outplanting,].department
        Individual.location_generated -> [Outplanting,].department
        Individual.name_generated -> Species.family.genus

    species:
        Family.full_name_generated -> self
        Species.full_name_generated -> Family.genus


Things a user can change - which needs recalculation 

- on Territory.save()
  - update Territory.name_generated
  - when code changed:
      - update all belonging Departments.full_code via Department.save()
        - call all belonging Individual.calc_outplantings()

- on Department.save()
  - update full_code
  - when changed: 
    - call all belonging Individual.calc_outplantings()
  - when Territory changed (Department moved to another Territory): 
    - call old and new Territory.calc_outplanting_fields()
    

"""


def calc_all():
    strip_whitespace()
    assign_territory()
    assign_ticket_types()
    calc_botanic_gardens()
    calc_species()
    calc_outplantings()
    fix_country_code()
    calc_individuals()


def calc_outplantings():
    with transaction.atomic():
        print("calc territories")
        count = Territory.objects.all().count()
        for i, self in enumerate(Territory.objects.all()):
            if i % 10 == 0:
                print("%s/%s" % (i, count))
            self.calc_outplanting_fields()
    with transaction.atomic():
        print("calc departments")
        count = Department.objects.all().count()
        for i, self in enumerate(Department.objects.all()):
            if i % 100 == 0:
                print("%s/%s" % (i, count))
            self.calc_outplanting_fields()


def calc_individuals_outplantings():
    with transaction.atomic():
        print("calc individuals")
        count = Individual.objects.all().count()
        for i, self in enumerate(Individual.objects.all()):
            if i % 1000 == 0:
                print("%s/%s" % (i, count))
            self.calc_outplantings()


def calc_botanic_gardens():
    with transaction.atomic():
        for self in BotanicGarden.objects.all():
            self.save()


def calc_species():
    with transaction.atomic():
        for self in Family.objects.all():
            self.save()
    with transaction.atomic():
        for self in Species.objects.all():
            self.save()


def calc_individuals():
    with transaction.atomic():
        for self in Territory.objects.all():
            self.save()
    with transaction.atomic():
        for self in Individual.objects.all():
            self.calc_outplantings(do_save=True)


def fix_country_code():
    for i in Individual.objects.filter(found_country="mne"):
        i.found_country = "me"
        i.save()
    for i in Individual.objects.filter(ipen_country="mne"):
        i.ipen_country = "me"
        i.save()


def assign_ticket_types():
    with transaction.atomic():
        for t in LaserGravurTicket.objects.all():
            if t.ticket_type != "laser":
                t.save()


def assign_territory():
    """Assign the correct Territory to all Departments
    and remove the Territory code from Department code"""
    with transaction.atomic():
        for d in Department.objects.filter(code__contains="-"):
            tcode = d.code.split("-")[0]
            try:
                d.territory = Territory.objects.get(code=tcode)
                d.code = d.code.split("-")[1]
                d.save()
            except Territory.DoesNotExist:
                pass
                #print("Territory '%s' not found!" % tcode)


def strip_whitespace():
    """Remove leading and trailing whitespace from all textfields"""
    Models = (Department, Territory, BotanicGarden, Family, Species, Individual, Seed)
    for Model in Models:
        for model in Model.objects.all():
            changes = []
            for field in model._meta.fields:
                if "generated" not in field.name and hasattr(model, field.name):
                    if isinstance(field, CharField):
                        text = getattr(model, field.name)
                        if text is not None:
                            stripped = text.strip().replace('\t', ' ')
                            if text != stripped:
                                changes.append("stripped '%s' [%s], was [%s]" % (field.name, stripped, text))
                                setattr(model, field.name, stripped)
            if changes:
                #print(u"Model %s (%s) '%s'" % (Model, model.id, model))
                for c in changes:
                    pass #$print("  " + c)
                try:
                    model.save()
                except IntegrityError as e:
                    pass
                    #print(u"ERROR %s" % e)
