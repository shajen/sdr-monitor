from django.utils import timezone
from django.utils.timezone import localtime
from sdr.models import *
from sdr.signals import decode_txt
import datetime
import logging
import sdr.utils.sound_classifier
import threading
import time


STATIC_BAND = [
    (87500000, 108000000, "WBFM"),
    (108000000, 137000000, "AM"),
]


class ClassifierController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__is_working = True
        self.__logger = logging.getLogger("Classifier")
        self.__sound_classifier = sdr.utils.sound_classifier.SoundClassifier()

    def get_media_class(self, t, modulation=""):
        try:
            modulation = modulation or t.modulation
            media_type = get_media_type(modulation)
            if media_type == "audio":
                return self.__sound_classifier.get_sound_label(t, modulation)
            elif media_type == "txt":
                process = decode_txt(
                    in_file=t.data_file.path,
                    modulation=modulation,
                    sample_rate=t.end_frequency - t.begin_frequency,
                    format="json",
                    duration=datetime.timedelta(seconds=5),
                )
                if process.stdout.read():
                    return ("Txt", 1.0)
                else:
                    return ("Unknown", 0.0)
            else:
                self.__logger.warning("transmission: %d, modulation: %s, unknown media type: %s" % (t.id, modulation, media_type))
                return ("Unknown", 0.0)
        except Exception as e:
            self.__logger.warning("transmission: %d, modulation: %s, media type: %s, exception: %s" % (t.id, modulation, media_type, e))
            return ("Unknown", 0.0)

    def get_modulation(self, t):
        for begin, end, modulation in STATIC_BAND:
            if begin <= t.bandwidth() and t.bandwidth() <= end:
                return (modulation, self.get_media_class(t, modulation))

        modulations = {}
        for modulation in AUDIO_MODULATIONS + TXT_MODULATIONS:
            modulations[modulation] = self.get_media_class(t, modulation)
        best_modulation = max(modulations, key=lambda k: modulations[k][1])
        if modulations[best_modulation][1] == 0.0:
            return ("Unknown", ("Unknown", 0.0))
        else:
            return (best_modulation, modulations[best_modulation])

    def run(self):
        default_modulation = get_default_modulation()
        default_media_class = get_default_media_class()
        self.__logger.debug("start")
        while self.__is_working:
            self.__logger.debug("processing")
            cut_dt = timezone.now() - timezone.timedelta(seconds=10)
            for t in Transmission.objects.filter(end_date__lt=cut_dt, media_class=default_media_class).order_by("begin_date").all():
                if t.modulation == default_modulation:
                    modulation, (media_class, accuracy) = self.get_modulation(t)
                    t.modulation = modulation
                    t.media_class = media_class
                    t.accuracy = accuracy
                    t.save()
                else:
                    media_class, accuracy = self.get_media_class(t)
                    t.media_class = media_class
                    t.accuracy = accuracy
                    t.save()
                self.__logger.info(
                    "id: %d, frequency: %d Hz, date: %s, duration: %s, modulation: %s, class: %s, accuracy: %.2f"
                    % (t.id, t.middle_frequency(), localtime(t.end_date.replace(microsecond=0)), t.duration(), t.modulation, t.media_class, accuracy)
                )
                if not self.__is_working:
                    break
            time.sleep(1)
        self.__logger.debug("stop")

    def stop(self):
        self.__is_working = False
