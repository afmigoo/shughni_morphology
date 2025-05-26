from pathlib import Path
import re
from string import punctuation

## Configuration
raw_corpus_dir = Path(__file__).parent.joinpath('raw_corpus')
corpus_dir = Path(__file__).parent.joinpath('corpus')
############ INPUT FILE
input_file = raw_corpus_dir.joinpath('shugni-test.txt')
############
_out_file = input_file.name.removesuffix('.txt')
output_file_cyr = corpus_dir.joinpath(f"{_out_file}-fit-cyr.txt")
output_file_lat = corpus_dir.joinpath(f"{_out_file}-fit-lat.txt")

## Processing
LAT = "aābvwgɣɣɣ̌dδeêžzӡiyīīkqlmnoprstθϑuūůfxx̌hcčšǰǰ"
CYR = "аāбвwгғғ̌ɣ̌дδеêжзȥийӣӣкқлмнопрстθθуӯу̊фхх̌ҳцчшҷҷ"
punct = punctuation.replace('-', '') + '–'

def process(line: str) -> str:
    line = line.lower().strip()
    line.replace(' ', ' ') # NO-BREAK SPACE 
    line = re.sub(r'[\u0301]', '', line) # removing stress diacritic
    line = re.sub(f'[{punct}]', '', line) # removing punctuation
    line = re.sub(r' +', ' ', line) # squishing spaces
    return line

def writing_score(line: str, charset: str) -> float:
    abs_score = sum(1 for ch in line if ch in charset)
    return abs_score / len(line)

with open(input_file, 'r', encoding='utf-8') as fi:
    with open(output_file_cyr, 'w', encoding='utf-8') as fo_cyr:
        with open(output_file_lat, 'w', encoding='utf-8') as fo_lat:
            for line in fi:
                line = process(line)
                if not line: 
                    continue
                if writing_score(line, LAT) > writing_score(line, CYR):
                    fo_lat.write(f"{line}\n")
                else:
                    fo_cyr.write(f"{line}\n")
            fo_lat.write('\n')
        fo_cyr.write('\n')
