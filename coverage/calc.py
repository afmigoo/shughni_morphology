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
    return [None if x[1] == 'inf' else x[0]
            for x in analyzed]

# GLOBAL COUNTERS
total = success = i = 0
analyzer = None
BATCH_SIZE = 5_000
words = []
def run():
    if not len(words): return
    global total, success, i
    analyzed = analyze(words, analyzer)
    words.clear()
    total += len(analyzed)
    success += sum(1 for x in analyzed if x)
    i += 1

for line in stdin:
    if analyzer is None:
        if writing_score(line, LAT) > writing_score(line, CYR):
            analyzer = ANALYZER_LAT
        else:
            analyzer = ANALYZER_CYR
    # reached end of file
    if line == '\n':
        run()
        analyzer = None
        continue
    words.extend(line.strip().split())
    if len(words) < BATCH_SIZE:
        continue
    run()

run()

print(f"Total:\t{total}\nPassed:\t{success}")
print(f"{success / total:.5f}")
