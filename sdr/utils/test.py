from django.test import TestCase
import sdr.utils.device


class DeviceTestCase(TestCase):
    def test_raw_name_converter(self):
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("hackrf_00000000"), "HackRF 0")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("hackrf_abcd1234"), "HackRF abcd1234")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("hackrf_00000000000000000000abcd1234"), "HackRF abcd1234")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("rtlsdr_abcd1234"), "RTL-SDR abcd1234")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("rtlsdr_0000ab12"), "RTL-SDR ab12")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("unknown_0000ab12"), "unknown ab12")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("unknown_abcd1234"), "unknown abcd1234")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("hackrf_00000000000000000000abcd1234_AMP00_LNA00_VGA00"), "HackRF abcd1234 AMP00 LNA00 VGA00")
        self.assertEqual(sdr.utils.device.convert_raw_to_name_to_pretty_name("test_00000000000000000000abcd1234_AMP00_LNA00_VGA00"), "test abcd1234 AMP00 LNA00 VGA00")
