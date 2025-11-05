def convert_raw_to_name_to_pretty_name(raw_name):
    prefix_map = {
        "hackrf": "HackRF",
        "rtlsdr": "RTL-SDR",
    }
    parts = raw_name.split("_")
    if len(parts) == 1:
        return raw_name
    prefix = parts[0]
    rest_parts = parts[1:]
    device_id = rest_parts[0].lstrip("0") or "0"
    extras = rest_parts[1:]
    pretty_prefix = prefix_map.get(prefix, prefix)
    pretty_name = " ".join([pretty_prefix, device_id] + extras)
    return pretty_name
