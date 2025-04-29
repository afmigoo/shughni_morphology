#!/usr/bin/env python3
from collections import Counter
from pprint import pprint
from pathlib import Path
from typing import Tuple, List, Iterable
from sys import stdin
import subprocess
from tabulate import tabulate

from src.hfst import parse_only_results, call_hfst_lookup

ANALYZER_CYR = Path(__file__).parent.parent.parent.joinpath('sgh_analyze_stem_word_cyr.hfstol')
ANALYZER_LAT = Path(__file__).parent.parent.parent.joinpath('sgh_analyze_stem_word_lat.hfstol')
results = Path(__file__).parent.joinpath('failed.txt')
results.unlink(missing_ok=True)

if not ANALYZER_CYR.exists():
    raise FileNotFoundError(f'Cyr analyzer not found: {ANALYZER_CYR}')
if not ANALYZER_LAT.exists():
    raise FileNotFoundError(f'Lat analyzer not found: {ANALYZER_LAT}')

LAT = "aābvwgɣɣɣ̌dδeêžzӡiyīīkqlmnoprstθϑuūůfxx̌hcčšǰǰ"
CYR = "аāбвwгғғ̌ɣ̌дδеêжзȥийӣӣкқлмнопрстθθуӯу̊фхх̌ҳцчшҷҷ"
def writing_score(line: str, charset: str) -> float:
    abs_score = sum(1 for ch in line if ch in charset)
    return abs_score / len(line)

def analyze(words: list[str]) -> list[str | None]:
    """Analyzes input words with hfst `ANALYZER`. Returns 
    a list of analyzed forms. Word is None if `ANALYZER` failed
    to analyze it.

    Returns:
        list[str | None]: List of analyzed words(str) or failed words(None)
    """
    if len(words) == 0:
        return []
    
    words = '\n'.join(words)
    if writing_score(words, LAT) > writing_score(words, CYR):
        analyzer_file = ANALYZER_LAT
    else:
        analyzer_file = ANALYZER_CYR
    
    analyzer = subprocess.Popen(["hfst-lookup", "-q", analyzer_file],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    res = analyzer.communicate(input=bytes(words, encoding='utf8'))[0].decode()
    analyzed = [x.split('\t')[1:] for x in res.split('\n\n') if x]
    return [x[0] for x in analyzed]

def fails_stats(analyzed: List[List[str]]) -> Tuple[Counter, Counter]:
    freq_word = Counter()
    freq_morph = Counter()
    
    for results in analyzed:
        if not '+?' in results[0]:
            continue
        word = results[0].replace('+?', '')

        if '-' in word: 
            for morph in word.split('-'):
                freq_morph[morph] += 1
        freq_word[word] += 1
    return freq_morph, freq_word

def dump_failed(failed: Iterable[str]):
    with open(results, 'a', encoding='utf-8') as out_f:
        out_f.writelines(line + '\n' for line in failed)

def main():
    lat_words: List[str] = []
    cyr_words: List[str] = []
    for line in stdin:
        if writing_score(line, LAT) > writing_score(line, CYR):
            lat_words.extend(line.strip().split())
        else:
            cyr_words.extend(line.strip().split())
    analyzed: List[List[str]] = []
    analyzed.extend(parse_only_results(call_hfst_lookup(ANALYZER_LAT, lat_words)))
    analyzed.extend(parse_only_results(call_hfst_lookup(ANALYZER_CYR, cyr_words)))
    assert len(lat_words) + len(cyr_words) == len(analyzed)
    del lat_words, cyr_words

    fail_morph, fail_word = fails_stats(analyzed)
    success = sum(1 for results in analyzed if not results[0].endswith('+?'))
    dump_failed(results[0] for results in analyzed if results[0].endswith('+?'))

    print('Coverage corpus')
    print(tabulate([['metric', 'value', 'absolute'],
                    ['coverage', f'{success / len(analyzed):.4f}', f'{success}/{len(analyzed)}']],
                    tablefmt="rounded_outline", headers='firstrow'))
    print(f"Top 5 unrecognized (morphs):")
    pprint(fail_morph.most_common(5))
    print(f"Top 5 unrecognized (words):")
    pprint(fail_word.most_common(5))
    print()

if __name__ == '__main__':
    main()
    #analyze("wuz-um as xu kōr bēzōr sut".split(' '), ANALYZER_LAT)
