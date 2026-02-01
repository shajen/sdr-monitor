from django.utils import timezone
from django.utils.timezone import localtime
from sdr.models import *
from sdr.signals import *
import logging
import sdr.signals
import sdr.utils.sound_classifier
import threading
import time


class ClassifierController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__is_working = True
        self.__logger = logging.getLogger("Classifier")
        self.__sound_classifier = sdr.utils.sound_classifier.SoundClassifier()

    def run(self):
        default_modulation = get_default_modulation()
        default_media_class = get_default_media_class()
        self.__logger.debug("start")
        while self.__is_working:
            self.__logger.debug("processing")
            cut_dt = timezone.now() - timezone.timedelta(seconds=10)
            for t in Transmission.objects.filter(end_date__lt=cut_dt, modulation=default_modulation, media_class=default_media_class).order_by("begin_date").all():
                self.__logger.info("id: %d, frequency: %d Hz, date: %s, duration: %s" % (t.id, t.middle_frequency(), localtime(t.end_date), t.duration()))
                if t.media_type == "audio":
                    self.__sound_classifier.update(t)
                elif t.media_type == "txt":
                    process = sdr.signals.decode_txt(
                        in_file=t.data_file.path,
                        modulation=t.modulation,
                        sample_rate=t.end_frequency - t.begin_frequency,
                        format="json",
                        duration=datetime.timedelta(seconds=10),
                    )
                    media_class = "Data" if process.stdout.read() else "Unknown"
                    t.media_class = media_class
                    self.__logger.info(
                        "id: %d, frequency: %d Hz, date: %s, duration: %s, class: %s" % (t.id, t.middle_frequency(), localtime(t.end_date), t.duration(), media_class)
                    )
                    t.save()
                if not self.__is_working:
                    break
            time.sleep(1)
        self.__logger.debug("stop")

    def stop(self):
        self.__is_working = False
