from sdr.models import *


def run(*args):
    Transmission.objects.update(audio_class=get_default_audio_class_id())
