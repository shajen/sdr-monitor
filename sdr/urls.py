import sdr.views
from django.urls import path

urlpatterns = [
    path("config/", sdr.views.config, name="sdr_config"),
    path("group/add/", sdr.views.add_group, name="sdr_add_group"),
    path("group/delete/<int:group_id>/", sdr.views.delete_group, name="sdr_delete_group"),
    path("groups/", sdr.views.groups, name="sdr_groups"),
    path("logs/", sdr.views.logs, name="sdr_logs"),
    path("satellites/", sdr.views.satellites, name="sdr_satellites"),
    path("spectrogram/<int:spectrogram_id>/", sdr.views.spectrogram, name="sdr_spectrogram"),
    path("spectrogram/<int:spectrogram_id>/data/", sdr.views.spectrogram_data, name="sdr_spectrogram_data"),
    path("spectrograms/", sdr.views.spectrograms, name="sdr_spectrograms"),
    path("transmission/<int:transmission_id>/", sdr.views.transmission, name="sdr_transmission"),
    path("transmission/<int:transmission_id>/data/", sdr.views.transmission_data, name="sdr_transmission_data"),
    path("transmissions/", sdr.views.transmissions, name="sdr_transmissions"),
]
