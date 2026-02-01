from django.utils.timezone import localtime
from sdr.models import *
import common.utils.classifier
import csv
import datetime
import io
import logging
import numpy as np
import sdr.signals


# https://www.tensorflow.org/lite/inference_with_metadata/task_library/audio_classifier
# https://tfhub.dev/google/yamnet/1
class SoundClassifier:
    def __init__(self):
        self.__logger = logging.getLogger("Sound")
        self.__classifier = common.utils.classifier.Classifier(model_path="ai/yamnet.tflite", labels=SoundClassifier.__get_labels())

    def __get_labels():
        with open("ai/yamnet_class_map.csv", "r") as file:
            class_map_csv = io.StringIO(file.read())
            class_names = [display_name for (_, _, display_name) in csv.reader(class_map_csv)]
            return class_names[1:]
        return []

    def __get_audio_class_name(self, name):
        if name in ["Speech", "Music", "Unknown"]:
            return name
        else:
            return "Noise"

    def get_sound_label(self, t):
        try:
            sample_rate = t.end_frequency - t.begin_frequency
            data = sdr.signals.decode_audio(t.data_file.path, None, t.group.modulation, sample_rate, out_rate=16000, duration=datetime.timedelta(seconds=10))
            data = np.frombuffer(data, dtype=np.float32)
            (sound_id, sound_label, accuracy) = self.__classifier.predict_class(data)
            self.__logger.info(
                "id: %d, frequency: %d Hz, date: %s, duration: %s, class: %s, accuracy: %.2f"
                % (t.id, t.middle_frequency(), localtime(t.end_date), t.duration(), sound_label, accuracy)
            )
            return sound_label
        except Exception as e:
            self.__logger.warning("exception: %s" % e)
            return "Unknown"

    def update(self, t):
        self.__logger.info("id: %d, frequency: %d Hz, date: %s, duration: %s" % (t.id, t.middle_frequency(), localtime(t.end_date), t.duration()))
        sound_label = self.get_sound_label(t)
        name = self.__get_audio_class_name(sound_label)
        t.audio_class = AudioClass.objects.get_or_create(name=name, subname=sound_label)[0]
        t.save()
