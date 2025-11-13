from django.db.models import F
from sdr.models import *


def update_groups():
    Transmission.objects.update(group_id=get_default_group_id())
    for group in Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency")).order_by("-bandwidth").all():
        Transmission.objects.annotate(frequency=(F("begin_frequency") + F("end_frequency")) / 2).filter(
            frequency__gte=group.begin_frequency, frequency__lte=group.end_frequency
        ).update(group_id=group.id)
