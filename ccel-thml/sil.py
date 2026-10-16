from pathlib import Path
import re

# SIL mappings from https://raw.githubusercontent.com/silnrsi/wsresources/refs/heads/master/scripts/Grek/legacy/sil-galatia/mappings/SILGreek.map

# Get the directory where this script is located
script_dir = Path(__file__).parent

# Combine the directory path with your filename
file_path = script_dir / "sil.txt"

mapping = {
    "a": "α",
    "e": "ε",
    "i": "ι",
    "j": "η",
    "o": "ο",
    "u": "υ",
    "w": "ω",
    "r": "ρ",

    '`': "\u0300",
    "'": "\u0301",
    '"': "\u0308",
    "h": "\u0313",
    "H": "\u0314",
    "^": "\u0342",
    "_": "\u0345"
}

MAPPING = {}

with open(file_path, "r") as f:
    for match in re.findall(r'0x([a-zA-Z0-9]+)\s*\<\>\s*\'([a-zA-Z0-9\'\"\_\^\`]+)\'\s*\"?(\')?\"?', f.read()):
        val = ''.join(match[1:])
        if len(val) > 1 and (val.startswith("h") or val.startswith("H")):
            val = val[1] + val[0] + val[2:]
        for (k, v) in mapping.items():
            val = val.replace(k, v)

        key = str(int(match[0], 16))
        MAPPING[key] = val
        
def convert_sil_to_unicode(text):

    pattern = r'&a?m?p?;?\s(\d+)[··]'

    def replace_entity(match):
        code_point = match.group(1)
        if not code_point in MAPPING:
            raise Exception(f"invalid code point {code_point} ({match})")

        # Substitute with mapped Greek character
        return MAPPING[code_point]

    return re.sub(pattern, replace_entity, text)

if __name__ == "__main__":
    test = ("οὔτε τῷ\n"
    "Υἱ&amp; 254·\n"
    "συνεξισούμενον")
    print(test)
    print(convert_sil_to_unicode(test))
    print("The root may be &#214;BA")
    print(convert_sil_to_unicode("The root may be &#214;BA"))