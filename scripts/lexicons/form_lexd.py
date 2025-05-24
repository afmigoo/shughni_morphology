from pathlib import Path
from typing import List, Tuple
import re
import csv
import os

from src.noun_fix import fix_nouns
from src.pron_fix import fix_pronouns
from src.verb_fix import replace_ending_td, replace_ending_ch

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
            if 'noun' in file.name and not 'irregular' in file.name:
                if 'pl' in file.name:
                    f.write(f'LEXICON {file2lexicon(file)}[{noun_tags[0]}]\n')
                else:
                    f.write(f'LEXICON {file2lexicon(file)}[{",".join(noun_tags)}]\n')
            else:
                f.write(f'LEXICON {file2lexicon(file)}\n')
    with open(file, 'a', encoding='utf-8') as f:
        for w, com in lines:
            f.write(f"{w}{' '*(comment_distance - len(w))}# {com}\n")    

def apply_fixes(lines: List[Tuple[str, str]], file: Path) -> List[Tuple[str, str]]:
    # adding noun tags
    if 'noun' in file.stem:
        fix_nouns(lines)
    # fixing inf stems
    if 'verb_inf' in file.stem:
        for i in range(len(lines)):
            lines[i] = (lines[i][0].removesuffix('оw'), lines[i][1])
    # fixing pst and inf stem endings
    if 'perf.csv' in file.stem:
        lines = replace_ending_ch(lines)
    # removing existing pronouns
    if 'pron' in file.stem:
        lines = fix_pronouns(lines)

    return lines

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
            if lines[i][1] in lines[cur_main][1]:
                new_meaning = ''
            else:
                new_meaning = f"; {lines[i][1]}"
            lines[cur_main] = (lines[cur_main][0], f"{lines[cur_main][1]}{new_meaning}")
            deleted.add(i)
    lines = [lines[i] for i in range(len(lines)) if not i in deleted]
    out_file = f'{file.stem}.lexd'
    lines = apply_fixes(lines, file)
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
