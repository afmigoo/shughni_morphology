from collections import Counter
from pprint import pprint
from pathlib import Path
from typing import Tuple
from sys import stdin
import subprocess

ANALYZER_CYR = Path(__file__).parent.parent.parent.joinpath('analyze_stem_word_cyr.hfst')
ANALYZER_LAT = Path(__file__).parent.parent.parent.joinpath('analyze_stem_word_lat.hfst')

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

def fails_stats(analyzed: list[str]) -> Tuple[Counter, Counter]:
    freq_word = Counter()
    freq_morph = Counter()
    
    for word in analyzed:
        if not '+?' in word:
            continue
        word = word.replace('+?', '')

        if '-' in word: 
            for morph in word.split('-'):
                freq_morph[morph] += 1
        else:
            freq_word[word] += 1
    return freq_morph, freq_word

def main():
    # GLOBALS
    BATCH_SIZE = 5_000
    words = [] # here batch is stored
    analyzed = [] # here the result is stored
    """ def run():
        if not len(words): return
        nonlocal total, success
        analyzed = analyze(words, analyzer)
        fails_stats(analyzed, fails_freq)
        words.clear() # clearing the batch
        total += len(analyzed)
        success += sum(1 for x in analyzed if not x.endswith('+?')) """
    
    # STARTING READING STDIN
    for line in stdin:
        # reached end of file, resetting analyser and processing leftover batch
        if line == '\n':
            analyzed.extend(analyze(words))
            words.clear()
            continue
        # adding to the batch
        words.extend(line.strip().split())
        # skipping if batch not large enough
        if len(words) < BATCH_SIZE:
            continue
        analyzed.extend(analyze(words))
        words.clear()
    analyzed.extend(analyze(words))
    words.clear()

    fail_morph, fail_word = fails_stats(analyzed)
    success = sum(1 for w in analyzed if not w.endswith('+?'))

    print(f"Total:\t{len(analyzed)}")
    print(f"Passed:\t{success}")
    print(f"Score:\t{success / len(analyzed):.5f}")
    print(f"Top 10 fails (morphs):")
    pprint(fail_morph.most_common(10))
    print(f"Top 10 fails (words):")
    pprint(fail_word.most_common(10))

if __name__ == '__main__':
    main()
    #analyze("wuz-um as xu kōr bēzōr sut".split(' '), ANALYZER_LAT)
