from pathlib import Path
import re
from string import punctuation

input_file = Path(__file__).parent.joinpath('raw_corpus/shugni-test.txt')
output_file = Path(__file__).parent.joinpath('corpus/shugni-test-fit.txt')

punct = punctuation.replace('-', '')
def process(line: str) -> str:
    line = line.lower()
    line = re.sub(r'[\u0301]', '', line) # removing stress diacritic
    line = re.sub(f'[{punct}]', '', line) # removing punctuation
    return line

with open(input_file, 'r', encoding='utf-8') as fi:
    with open (output_file, 'w', encoding='utf-8') as fo:
        for line in fi:
            fo.write(process(line))
