from sdr.models import *


def run(*args):
    Transmission.objects.update(modulation=get_default_modulation(), media_class=get_default_media_class(), accuracy=0.0)
