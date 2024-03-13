import re, os, csv
"""
from flask import request, render_template, Markup
from bs4 import BeautifulSoup

try:
    from karamshoev import app
except ModuleNotFoundError:
    pass
try:
    import BeautifulSoup
except ModuleNotFoundError:
    pass
"""
current_folder = os.path.dirname(os.path.abspath(__file__))
ortho_file_path = os.path.join(current_folder, os.path.join("static", "ortho.txt"))
ortho_cyr_file_path = os.path.join(current_folder, os.path.join("static", "ortho_cyr.txt"))
ortho_table_path = os.path.join(current_folder, os.path.join("static", "ortho_table.csv"))

problem_symbols = ("gamma", "gh_ipa", "j", "sh")
cyr_check = "[ПпБЛлЖжШшФфЦцЧчИи]"
cyr_precise_check = "[аāбвгдежзиӣйклмнопрстуӯфхцчшщъьыэюяқғӽҷ]"
lat_check = "[SsVvFfIiGgZzQqN]"
lat_precise_check = "[aābcdefghiījklmnopqrstuūůvxyzčžš]"


class ConverterOutput:

    def __init__(self, text, base, code):
        self.text = text
        self.base = base
        self.code = code

    def __repr__(self):
        return self.text

    def full(self):
        return f"ConverterOutput(text='{self.text}', base='{self.base}', code='{self.code}'"


class Converter:
    """The main class to convert from alphabet X to alphabet Y.

    Make a `Converter` object. Optionally, set the default destination alphabet as an argument:
    > c = Converter(dest="cyr")

    List of possible destinations: "lat" (phonematic Latin transcription),
    "cyr" (Cyrillic alphabet), "ipa" (phonematic transcription
    with the International Phonetic alphabet).
    
    Then use the method `convert` to change the alphabet of a text:
    > converted_text = c.convert(original_text)
    > converted_text = c.convert(original_text, dest="ipa")
    """
    
    def __init__(self, dest="lat", settings="auto"):
        self._cyr = ("cyr", "cyrillic", "кир", "кириллица")
        self._lat = ("lat", "latin", "лат", "латиница")
        with open(ortho_table_path, 'r', encoding='utf-8-sig') as f:  # encoding 'utf-8-sig' helps to get rid
            reader = csv.reader(f, delimiter=";")  # of some technical .csv symbols
            self._ortho = {}
            headers = []
            for row in reader:
                if row[0] == "src":
                    headers = row
                else:
                    self._ortho[row[0]] = {headers[i]: row[i] for i in range(1, len(row))}
        
        self.settings = {
            "gamma": "auto",
            "gh_ipa": "auto",
            "j": "auto",
            "sh": "auto"
        } if settings == "auto" else self.settings
        self.orig = None
        if dest in self._lat:
            self.dest = self._lat[0]
        elif dest in self._cyr:
            self.dest = self._cyr[0]
        else:
            self.dest = dest

    def __repr__(self):
        return f"Converter(dest='{self.dest}', settings={self.settings})"
    
    def convert(self, text, dest=None):
        if dest is None:
            dest = self.dest
        text = re.sub("ǰ", "ǰ", text)  # replacing an especially tricky symbol
        self.orig, code = definecode(text, self.settings)  # defining base and code of the script
        text = fixbase(self.orig, text)  # fixing some problems (if necessary)
        text = changecode(code, text, dest, self._ortho)  # converting symbols
        return ConverterOutput(text, self.orig, code)


def definecode(text, settings):
    """Defines base, aka cyrillic or latin script is used in the text, and what contradictory symbols mean"""

    # trying to define whether the text is written in cyrllic or latin script
    if len(text) > 20 or len(re.findall(" ", text)) > 3:
        cyr_sum = len(re.findall(cyr_check, text))
        lat_sum = len(re.findall(lat_check, text))
        coeff = 6

    else:
        cyr_sum = len(re.findall(cyr_precise_check, text.lower()))
        lat_sum = len(re.findall(lat_precise_check, text.lower()))
        coeff = 1

    if cyr_sum > lat_sum * coeff:
        base = "cyr"
    elif lat_sum > cyr_sum * coeff:
        base = "lat"
    else:
        base = "unknown"

    code = {}
    for symbol in problem_symbols:
        code[symbol] = "unknown"

    if len(re.findall("[Ss]h", text)) == 0:
        code["sh"] = "символ не найден"

    elif settings["sh"] == "auto":  # if the setting is to determine phonematic meaning of 'sh' automatically

        if len(re.findall("[ШшŠšɕ]", text)) == 0:  # if there is no different symbol which means 'sch' in the text
            code["sh"] = "sch"                     # sh must mean 'sch'

        else:                                      # if there is a different symbol which means 'sch' in the text
            code["sh"] = "skh"                     # sh must mean 'skh'

    else:
        code["sh"] = settings["sh"]  # if user has indicated how sh should be interpreted, this indication is used

    if len(re.findall("[Γγ][^̌]|[Γγ]$", text)) == 0:  # if symbol γ is not found in the text
        code["gamma"] = "символ не найден"

    elif settings["gamma"] == "auto":

        if len(re.findall("[Γγ]̌|[Гг]̌|[Ѓѓ][ЪъЬь]|[Ұұ]", text)) > 0:  # if there is a different symbol
            code["gamma"] = "uvular"                                # which means 'velar' in the text
                                                                    # γ must mean 'uvular'

        elif len(re.findall("[ЃѓʁҒғ]|[Ɣɣ][^̌]|[Ɣɣ]$", text)) > 0:  # if there is a different symbol
            code["gamma"] = "velar"                               # which means 'uvular' in the text
                                                                  # γ must mean 'velar'

        else:  # if there are no symbols for determination in the text
            code["gamma"] = "uvular"
    else:
        code["gamma"] = settings["gamma"]  # if user has indicated how γ should be interpreted, this indication is used

    if len(re.findall("[Ɣɣ][^̌]|[Ɣɣ]$", text)) == 0:  # if symbol ɣ is not found in the text
        code["gh_ipa"] = "символ не найден"

    elif settings["gh_ipa"] == "auto":
        # checking whether there are different symbols which mean 'gh_ipa' in the text
        isthere = {"other_velar": False, "gh_ipa_hachek": False, "other_uvular": False}

        # if there is a different symbol which means 'velar' in the text
        if len(re.findall("[Гг]̌|[Ѓѓ][ЪъЬь]|[Ұұ]", text)) > 0:
            isthere["other_velar"] = True

        # if there is symbol ɣ with hachek in the text
        if len(re.findall("[Ɣɣ]̌", text)) > 0:
            isthere["gh_ipa_hachek"] = True

        # if there is a different symbol which means 'uvular' in the text
        if len(re.findall("[ЃѓʁҒғ]", text)) > 0:
            isthere["other_uvular"] = True

        if isthere["other_uvular"] == False:
            code["gh_ipa"] = "uvular"

        elif isthere["gh_ipa_hachek"] == False and isthere["other_velar"] == False:
            code["gh_ipa"] = "velar"

    else:
        code["gh_ipa"] = settings["gh_ipa"]  # if user has indicated how ɣ should be interpreted,
                                             # this indication is used

    if len(re.findall("[Jj][^̌]|[Jj]$", text)) == 0:  # if symbol j is not found in the text
        code["j"] = "символ не найден"

    elif settings["j"] == "auto":

        if len(re.findall("[ЙйYy]", text)) == 0:  # if symbols й/y are not found, j must mean 'y'
            code["j"] = "y"

        elif len(re.findall("[Jj]̌|[ǰЉљҶҷ]", text)) == 0:  # if there is a different symbol which means 'dzh',
            code["j"] = "dzh"                             # j must mean 'dzh'

        elif len(re.findall("[ȤȥƷӡ]|[Зз][ъ̌]", text)) == 0:  # if there is a different symbol which means 'dz',
            code["j"] = "dz"                                # j must mean 'dz'
    else:
        code["j"] = settings["j"]  # if user has indicated how j should be interpreted,
                                   # this indication is used

    return base, code


def fixbase(base, text):
    """If the base is latin but there are random cyrillic letters in the text, they are fixes"""

    changer = [
        ["С", "C"],
        ["с", "c"],
        ["К", "K"],
        ["к", "k"],
        ["М", "M"],
        ["м", "m"],
        ["Н", "H"],
        ["Р", "P"],
        ["р", "p"],
        ["Т", "T"],
        ["т", "t"],
        ["У", "Y"],
        ["у", "y"],
        ["А", "A"],
        ["а", "a"],
        ["Е", "E"],
        ["е", "e"],
        ["В", "B"],
        ["О", "O"],
        ["о", "o"],
        ["Х", "X"],
        ["х", "x"]
    ]

    if base != "?":
        for symbol in changer:
            if base == "lat":
                text = re.sub(symbol[0], symbol[1], text)
            elif base == "cyr":
                text = re.sub(symbol[1], symbol[0], text)

    return text


def bad_to_good(text, path, for_dict, lang_id):
    with open(path, 'r', encoding='UTF-8') as file:
        ortho = file.readlines()  # loading ortho.txt which contains replacement table

    for line in ortho:

        if line.startswith("/"):
            if for_dict:
                continue
            else:
                line = line[1:]

        if line.startswith("@"):
            if lang_id != 1:
                continue
            else:
                line = line[1:]

        if not line.startswith('#'):  # lines with hash in ortho.txt are user notes
            bad, good = line.split(' ')

            good = good[0:len(good) - 1]  # all the 'bad' symbols are replaced with corresponding 'good' symbols
            text = re.sub(bad, good, text)

    return text


def ortho_change(text, dest, dest_ortho):
    for letter in dest_ortho:
        text = re.sub(letter, dest_ortho[letter][dest], text)
    return text


def changecode(code, text, dest="lat", dest_ortho=[], for_dict=False, lang_id=1):
    """Converts the orthography"""

    text = re.sub("́", "", text)  # deleting accentuation marks

    if code["gamma"] == "velar":
        text = re.sub("Γ([^̌])", "Ɣ̌\1", text)  # replacing γ —> ɣ̌
        text = re.sub("γ([^̌])", "ɣ̌\1", text)

    if code["gh_ipa"] == "velar":
        text = re.sub("([Ɣɣ])([^̌])", r"\1̌\2", text)  # replacing ɣ —> ɣ̌

    if code["j"] == "y":
        text = re.sub("J([^̌])|J$", r"Y\1", text)  # replacing j —> y
        text = re.sub("j([^̌])|j$", r"y\1", text)

    elif code["j"] == "dz":
        text = re.sub("J([^̌])|J$", r"Ȥ\1", text)  # replacing j —> dz
        text = re.sub("j([^̌])|j$", r"ȥ\1", text)

    if code["sh"] == "sch":
        text = re.sub("S[Hh]", "Š", text)  # replacing sh —> š
        text = re.sub("sh", "š", text)

    text = bad_to_good(text=text, path=ortho_file_path, for_dict=for_dict, lang_id=lang_id)

    text = re.sub("̣", "", text)  #deleting Combining dot below

    text = ortho_change(text=text, dest=dest, dest_ortho=dest_ortho)

    return text

