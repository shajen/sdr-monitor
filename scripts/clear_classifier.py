from sdr.models import *


def run(*args):
    Transmission.objects.update(media_class=get_default_media_class())
