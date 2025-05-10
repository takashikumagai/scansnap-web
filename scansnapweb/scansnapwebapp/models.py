from django.db import models
from django.utils.translation import gettext_lazy as _

class Scan(models.Model):
    class Status(models.TextChoices):
        NOT_EXECUTED = "not_executed", _("Not_executed")
        SUCCESS = "success", _("Success")
        FAILED = "failed", _("Failed") # papers jammed in the ADF, etc.

    class Color(models.TextChoices):
        COLOR = "color", _("Color")
        GRAYSCALE = "grayscale", _("Grayscale")

    class Sides(models.TextChoices):
        DUPLEX = "duplex", _("Duplex")
        FRONT = "front", _("Front")

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NOT_EXECUTED)
    num_scanned_papers = models.IntegerField(default=0)
    paper_width = models.IntegerField(default=0)
    paper_height = models.IntegerField(default=0)
    color = models.CharField(max_length=16, choices=Color.choices, default=Color.COLOR)
    starting_page_number = models.IntegerField(default=1)
    sides = models.CharField(max_length=8, choices=Sides.choices, default=Sides.DUPLEX)
