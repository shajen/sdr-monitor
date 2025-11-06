from sdr.models import *


def run(*args):
    print("Devices: %d" % (Device.objects.count()))
    print("Transmissions: %d" % (Transmission.objects.count()))
    print("Spectrograms: %d" % (Spectrogram.objects.count()))
    print("GainTest: %d" % (GainTest.objects.count()))

    Device.objects.all().delete()
    Transmission.objects.all().delete()
    Spectrogram.objects.all().delete()
    GainTest.objects.all().delete()
