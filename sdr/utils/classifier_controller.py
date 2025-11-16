from django.utils import timezone
from sdr.models import *
from sdr.signals import *
import logging
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
        default_audio_class_id = get_default_audio_class_id()
        self.__logger.debug("start")
        while self.__is_working:
            self.__logger.debug("processing")
            cut_dt = timezone.now() - timezone.timedelta(seconds=10)
            for t in Transmission.objects.filter(end_date__lt=cut_dt, audio_class_id=default_audio_class_id).order_by("begin_date").all():
                if t.group.modulation in ["FM", "AM"]:
                    self.__sound_classifier.update(t)
                if not self.__is_working:
                    break
            time.sleep(1)
        self.__logger.debug("stop")

    def stop(self):
        self.__is_working = False
