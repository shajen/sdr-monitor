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
        default_audio_class_id = get_default_audio_class_id()
        self.__logger.debug("start")
        while self.__is_working:
            self.__logger.debug("processing")
            cut_dt = timezone.now() - timezone.timedelta(seconds=10)
            for t in Transmission.objects.filter(end_date__lt=cut_dt, audio_class_id=default_audio_class_id, group__data_type__in=["audio", "txt"]).order_by("begin_date").all():
                self.__logger.info("id: %d, frequency: %d Hz, date: %s, duration: %s" % (t.id, t.middle_frequency(), localtime(t.end_date), t.duration()))
                if t.group.data_type == "audio":
                    self.__sound_classifier.update(t)
                elif t.group.data_type == "txt":
                    process = sdr.signals.decode_txt(
                        in_file=t.data_file.path,
                        modulation=t.group.modulation,
                        sample_rate=t.end_frequency - t.begin_frequency,
                        format="json",
                        duration=datetime.timedelta(seconds=10),
                    )
                    (name, subname) = ("Data", "Data") if process.stdout.read() else ("Noise", "Unknown")
                    t.audio_class = AudioClass.objects.get_or_create(name=name, subname=subname)[0]
                    self.__logger.info("id: %d, frequency: %d Hz, date: %s, duration: %s, class: %s" % (t.id, t.middle_frequency(), localtime(t.end_date), t.duration(), name))
                    t.save()
                if not self.__is_working:
                    break
            time.sleep(1)
        self.__logger.debug("stop")

    def stop(self):
        self.__is_working = False
