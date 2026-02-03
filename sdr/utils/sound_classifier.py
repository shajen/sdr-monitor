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

    def __get_media_class_name(self, name, accuracy):
        if name in ["Speech"]:
            return (name, float(accuracy))
        else:
            return ("Unknown", 0.0)

    def get_sound_label(self, t, modulation=""):
        sample_rate = t.end_frequency - t.begin_frequency
        process = sdr.signals.decode_audio(
            in_file=t.data_file.path,
            format="f32le",
            modulation=modulation or t.modulation,
            sample_rate=sample_rate,
            out_rate=16000,
            duration=datetime.timedelta(seconds=10),
        )
        data = process.stdout.read()
        data = np.frombuffer(data, dtype=np.float32)
        (_, sound_label, accuracy) = self.__classifier.predict_class(data)
        return self.__get_media_class_name(sound_label, accuracy)
