def convert_raw_to_name_to_pretty_name(raw_name):
    prefix_map = {
        "hackrf": "HackRF",
        "rtlsdr": "RTL-SDR",
    }
    if "_" not in raw_name:
        return raw_name
    prefix, rest = raw_name.split("_", 1)
    rest = rest.lstrip("0") or "0"
    pretty_prefix = prefix_map.get(prefix.lower(), prefix.capitalize())
    return f"{pretty_prefix} {rest}"
