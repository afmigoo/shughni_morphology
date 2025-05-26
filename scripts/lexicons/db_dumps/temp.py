import csv
from pathlib import Path
import re

_root = Path(__file__).parent

inp = _root.joinpath('verb_perf_pl.csv_')
irregular_file = _root.joinpath('verb_perf_pl_irregular.csv')
regular_file = _root.joinpath('verb_perf_pl_regular.csv')

VoicelessConsonant = 'пткфθсшхх̌ҳцчқ'
Nasal = 'нм'
Liquid = 'лр'

VoicedObstruent = 'бдгвδзжӡzžȥɣ̌ɣҷғғ̌'
Vowel = 'аāеêиӣӣоуӯу̊'
Semivowel = 'wй'

regular_endings = {
    'ч': VoicelessConsonant+Nasal+Liquid,
    'ҷ': VoicedObstruent+Vowel+Semivowel,
}

with open(inp, 'r', encoding='utf-8') as fin, \
     open(irregular_file, 'w', encoding='utf-8') as firr, \
     open(regular_file, 'w', encoding='utf-8') as fr:
    reader, irregular_writer, regular_writer = csv.reader(fin), csv.writer(firr), csv.writer(fr)
    cols = next(reader)
    irregular_writer.writerow(cols); regular_writer.writerow(cols)

    for row in reader:
        is_reg = False
        for end, prev_letters in regular_endings.items():
            if re.match(f'^.*[{prev_letters}]{end}$', row[0]):
                regular_writer.writerow((row[0].removesuffix(end), row[1]))
                is_reg = True
                break
        if not is_reg:
            irregular_writer.writerow(row)
