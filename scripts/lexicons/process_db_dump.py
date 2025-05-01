from pathlib import Path
from typing import List, Tuple
import re
import csv
import os

input_dir = Path(__file__).parent.joinpath('db_dumps')
output_dir = Path(__file__).parent.parent.parent.joinpath('lexd/lexicons')

comment_distance = 25

fixes = {
    'ӯ̊': 'ӯ', # invalid set of diacritics
    'ҳ̌': 'ҳ',
    'ц̌': 'ч',
    '́': '' # remove stress
}

noun_tags = ['pl_all', 'sg']
noun_plurals = {
    'pl_in-laws': ['свояк', 'своячн', 'зять', 'невестка', 'тесть', 'деверь', 'шурин', 'теща', 'свекровь'],
    'pl_cousins': ['двоюродный брат', 'двоюродная сестра'],
    'pl_sisters': ['сестра', 'сестричка'],
    'pl_timesOfDay': ['утро', 'утрен', 'день', 'дневн', 'вечер', 'ночь', 'ночн', 'сумерки', 'закат', 'восход'],
    'pl_timesOfYear': ['весна', 'зима', 'лето', 'осень'],
}

def is_a_word(word: str) -> bool:
    return not ' ' in word and \
           not word.startswith('-')

def fix(word: str) -> str:
    for bad, good in fixes.items():
        word = word.replace(bad, good)
    return word

def file2lexicon(file: Path) -> str:
    return 'Lexicon' + ''.join(x.capitalize() for x in file.stem.split('_'))

def write_lexicon(file: Path, lines: List[Tuple[str, str]]):
    if not file.exists():
        with open(file, 'w', encoding='utf-8') as f:
            if 'noun' in file.name:
                f.write(f'LEXICON {file2lexicon(file)}[{",".join(noun_tags)}]\n')
            else:
                f.write(f'LEXICON {file2lexicon(file)}\n')
    with open(file, 'a', encoding='utf-8') as f:
        for w, com in lines:
            f.write(f"{w}{' '*(comment_distance - len(w))}# {com}\n")    

def process(file: Path) -> None:
    # reading lines in a list of tuples
    # and filtering out non-words
    lines = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        _, _ = next(reader)
        lines = [(w.lower(), com) for w, com in reader if is_a_word(w)]
        lines = [(fix(w), com.replace('\n', '')) for w, com in lines]

    # sorting lines alphabetically
    lines.sort()
    # merging dublicate words with different meanings
    cur_main = 0
    deleted = set()
    for i in range(1, len(lines)):
        if lines[i][0] != lines[cur_main][0]:
            cur_main = i
        else:
            lines[cur_main] = (lines[cur_main][0], f"{lines[cur_main][1]}; {lines[i][1]}")
            deleted.add(i)
    lines = [lines[i] for i in range(len(lines)) if not i in deleted]
    # adding gender tag if present
    out_file = f'{file.stem}.lexd'
    allowed_tags = ['f', 'm']
    tag = ''
    for t in allowed_tags:
        if file.stem.endswith(f'_{t}'):
            tag = t
    if tag != '':
        out_file = out_file.replace(f'_{tag}', '')
        for i in range(len(lines)):
            lines[i] = (f'{lines[i][0]}[{tag}]', lines[i][1])
    # adding noun tags
    if 'noun' in file.stem:
        for i in range(len(lines)):
            for tag, triggers in noun_plurals.items():
                found = False
                for trig in triggers:
                    if trig in lines[i][1]:
                        lines[i] = (f'{lines[i][0]}[{tag}]', lines[i][1])
                        found = True
                        break
                if found: 
                    break
    # fixing inf stems
    if 'verb_inf' in file.stem:
        for i in range(len(lines)):
            lines[i] = (lines[i][0].removesuffix('оw'), lines[i][1])
                
    # writing words
    write_lexicon(output_dir.joinpath(out_file), lines)

if __name__ == '__main__':
    for f in output_dir.iterdir():
        if f.is_file():
            f.unlink()
    csv_files = [input_dir.joinpath(f) 
                 for f in os.listdir(input_dir) 
                 if f.endswith('.csv')]
    csv_files.sort()
    for f in csv_files:
        process(f)
