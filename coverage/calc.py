from sys import stdin
import subprocess
from pathlib import Path

ANALYZER_CYR = Path(__file__).parent.parent.joinpath('shugni.anal.hfst')
ANALYZER_LAT = Path(__file__).parent.parent.joinpath('shugni.anal.latin.hfst')

LAT = "aābvwgɣɣɣ̌dδeêžzӡiyīīkqlmnoprstθϑuūůfxx̌hcčšǰǰ"
CYR = "аāбвwгғғ̌ɣ̌дδеêжзȥийӣӣкқлмнопрстθθуӯу̊фхх̌ҳцчшҷҷ"
def writing_score(line: str, charset: str) -> float:
    abs_score = sum(1 for ch in line if ch in charset)
    return abs_score / len(line)

def analyze(words: list[str], analyzer_file: Path) -> list[str | None]:
    """Analyzes input words with hfst `ANALYZER`. Returns 
    a list of analyzed forms. Word is None if `ANALYZER` failed
    to analyze it.

    Returns:
        list[str | None]: List of analyzed words(str) or failed words(None)
    """
    words = '\n'.join(words)
    analyzer = subprocess.Popen(["hfst-lookup", "-q", analyzer_file],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    res = analyzer.communicate(input=bytes(words, encoding='utf8'))[0].decode()
    analyzed = [x.split('\t')[1:] for x in res.split('\n\n') if x]
    return [x[0] for x in analyzed]

def fails_stats(analyzed: list[str], freq: dict) -> None:
    def inc_freq(word: str):
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    
    for word in analyzed:
        if '+?' in word:
            word = word.replace('+?', '')
        else:
            continue
        if '-' in word: 
            for morph in word.split('-'):
                inc_freq(f"-{morph}")
        else:
            inc_freq(word)

if __name__ == '__main__':
    # GLOBAL COUNTERS
    total = success = 0
    analyzer = None # analyzer file to use (lat or cyr one)
    fails_freq = {}
    BATCH_SIZE = 5_000
    words = [] # here batch is stored
    def run():
        if not len(words): return
        global total, success, i
        analyzed = analyze(words, analyzer)
        fails_stats(analyzed, fails_freq)
        words.clear() # clearing the batch
        total += len(analyzed)
        success += sum(1 for x in analyzed if not x.endswith('+?'))
    
    # STARTING READING STDIN
    for line in stdin:
        # determining writing (cyr or lat) if no analyser set
        if analyzer is None:
            if writing_score(line, LAT) > writing_score(line, CYR):
                analyzer = ANALYZER_LAT
            else:
                analyzer = ANALYZER_CYR
        # reached end of file, resetting analyser and processing leftover batch
        if line == '\n':
            run()
            analyzer = None
            continue
        # adding to the batch
        words.extend(line.strip().split())
        # skipping if batch not large enough
        if len(words) < BATCH_SIZE:
            continue
        run()

    run()

    sorted_fails = sorted(fails_freq.items(), key=lambda x: x[1], reverse=True)

    print(f"Total:\t{total}\nPassed:\t{success}")
    print(f"{success / total:.5f}")
    print(f"Top 20 fails: {sorted_fails[:20]}")
