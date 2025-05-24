import csv
from pathlib import Path

_root = Path(__file__).parent

inp = _root.joinpath('verb_perf_pl.csv')
irregular_file = _root.joinpath('verb_perf_pl_irregular.csv')
regular_file = _root.joinpath('verb_perf_pl_regular.csv')

regular_endings = [
    'ч',
    'ҷ',
]

with open(inp, 'r', encoding='utf-8') as fin, \
     open(irregular_file, 'w', encoding='utf-8') as firr, \
     open(regular_file, 'w', encoding='utf-8') as fr:
    reader, irregular_writer, regular_writer = csv.reader(fin), csv.writer(firr), csv.writer(fr)
    cols = next(reader)
    irregular_writer.writerow(cols); regular_writer.writerow(cols)

    for row in reader:
        is_reg = False
        for end in regular_endings:
            if row[0].endswith(end):
                regular_writer.writerow((row[0].removesuffix(end), row[1]))
                is_reg = True
                break
        if not is_reg:
            irregular_writer.writerow(row)
