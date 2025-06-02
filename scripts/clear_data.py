from sdr.models import *


def run(*args):
    print("Transmissions: %d" % (Transmission.objects.count()))
    print("Spectrograms: %d" % (Spectrogram.objects.count()))

    Transmission.objects.all().delete()
    Spectrogram.objects.all().delete()
