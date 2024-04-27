from pathlib import Path
import csv

file = Path(__file__).parent.joinpath('db_noun.csv')
out_file = Path(__file__).parent.joinpath('out_noun.txt')
comment_distance = 35

def is_bad(word: str) -> bool:
    return ' ' in word

# reading lines in a list of tuples
# and filtering out bad ones
lines = []
with open(file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    _, _ = next(reader)
    lines = [(w.lower(), com) for w, com in reader if not is_bad(w)]

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
# writing words
with open(out_file, 'w', encoding='utf-8') as fo:
    for w, com in lines:
        fo.write(f"{w}{' '*(comment_distance - len(w))}# {com}\n")
