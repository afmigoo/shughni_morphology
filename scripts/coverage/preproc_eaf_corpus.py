from pathlib import Path
from unicodedata import category
import os
import sys
import re
from pprint import pprint

from pympi.Elan import Eaf

root_dir = Path(__file__).parent
# dirs where script takes eaf files from
# all eaf files in dir `raw_corpus/example_name/*.eaf` 
# will be processed and saved in a single `corpus/example_name.txt` file
eaf_dirs = [root_dir.joinpath('raw_corpus/bible_luke'),
            root_dir.joinpath('raw_corpus/misc'),
            root_dir.joinpath('raw_corpus/pear')]

punctuation_chars = ''.join([chr(i) for i in range(sys.maxunicode) 
                             if category(chr(i)).startswith("P")])
punct = punctuation_chars.replace('-', '') + '–'

def process_line(line: str) -> str:
    line = line.lower()
    line.replace(' ', ' ') # NO-BREAK SPACE 
    line = re.sub(r'[\u0301]', '', line) # removing stress diacritic
    line = line.replace('á', 'a')
    line = re.sub(f'[{punct}0-9]', '', line) # removing punctuation and numbers
    line = re.sub(r' +', ' ', line) # squishing spaces
    line = line.replace('=', '-')
    return line.strip()

def process_eaf_dir(eaf_dir: Path) -> None:
    out_file = root_dir.joinpath(f'corpus/{eaf_dir.name}.txt')
    eaf_files = [eaf_dir.joinpath(f) for f in os.listdir(eaf_dir)]

    with open(out_file, 'w', encoding='utf-8') as fo:
        for eaf_file in eaf_files:
            eaf = Eaf(eaf_file)
            tier_name = list(eaf.get_tier_names())[0]
            annotations = eaf.get_annotation_data_for_tier(tier_name)
            for ann in annotations:
                fo.write(process_line(ann[2]) + '\n')

if __name__ == '__main__':
    for dir_name in eaf_dirs:
        process_eaf_dir(dir_name)
