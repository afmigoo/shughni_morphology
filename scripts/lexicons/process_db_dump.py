from pathlib import Path
import csv
import os

input_dir = Path(__file__).parent.joinpath('db_dumps')
output_dir = Path(__file__).parent.joinpath('lexd_lexicons')

comment_distance = 25

fixes = {
    'ӯ̊': 'ӯ'
}

def is_a_word(word: str) -> bool:
    return not ' ' in word and \
           not word.startswith('-')

def fix(word: str) -> str:
    for bad, good in fixes.items():
        word = word.replace(bad, good)
    return word

def process(file: Path, out_file) -> None:
    # reading lines in a list of tuples
    # and filtering out non-words
    lines = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        _, _ = next(reader)
        lines = [(w.lower(), com) for w, com in reader if is_a_word(w)]
        lines = [(fix(w), com) for w, com in lines]

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
    allowed_tags = ['f', 'm']
    tag = ''
    for t in allowed_tags:
        if file.stem.endswith(f'_{t}'):
            tag = t
    if tag != '':
        for i in range(len(lines)):
            lines[i] = (f'{lines[i][0]}[{tag}]', lines[i][1])
    # writing words
    with open(out_file, 'w', encoding='utf-8') as fo:
        for w, com in lines:
            fo.write(f"{w}{' '*(comment_distance - len(w))}# {com}\n")

if __name__ == '__main__':
    csv_files = [input_dir.joinpath(f) 
                 for f in os.listdir(input_dir) 
                 if f.endswith('.csv')]
    for f in csv_files:
        process(f, output_dir.joinpath(f'{f.stem}.txt'))
