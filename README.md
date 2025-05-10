# Introduction

This project is part of a larger `SDR` project called [https://github.com/shajen/sdr-hub](https://github.com/shajen/sdr-hub). Please familiar with it before starting work.

Sdr monitr is responsible for saving and decoding data received from [https://github.com/shajen/rtl-sdr-scanner-cpp](https://github.com/shajen/rtl-sdr-scanner-cpp). It allows easy access to data via web panel. It is also responsible for decoding raw data into wav files. For now, it supports `FM` and `AM` modulations.

# AI

It uses `AI` model from [https://www.tensorflow.org/lite/inference_with_metadata/task_library/audio_classifier](https://www.tensorflow.org/lite/inference_with_metadata/task_library/audio_classifier) to classify whether a transmission is speech or noise.

# Quickstart

Instructions [here](https://github.com/shajen/sdr-hub?tab=readme-ov-file#quickstart).

# Build from sources

Clone repository (**do not forget to sync submodules!**) and run:

```
docker build -t shajen/sdr-monitor .
```

# Contributing

In general don't be afraid to send pull request. Use the "fork-and-pull" Git workflow.

1. **Fork** the repo
2. **Clone** the project to your own machine
3. **Commit** changes to your own branch
4. **Push** your work back up to your fork
5. Submit a **Pull request** so that we can review your changes

NOTE: Be sure to merge the **latest** from **upstream** before making a pull request!

# Donations

If you enjoy this project and want to thanks, please use follow link:

- [PayPal](https://www.paypal.com/donate/?hosted_button_id=6JQ963AU688QN)

- [Revolut](https://revolut.me/borysm2b)

- BTC address: 18UDYg9mu26K2E3U479eMvMZXPDpswR7Jn

# License

[![License](https://img.shields.io/:license-GPLv3-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl.html)

- *[GPLv3 license](https://www.gnu.org/licenses/gpl.html)*
