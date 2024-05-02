from sys import stdin
import subprocess
from pathlib import Path

ANALYZER_FILE = Path(__file__).parent.parent.joinpath('shugni.anal.hfst')

def analyze(words: list[str]) -> list[str | None]:
    """Analyzes input words with hfst `ANALYZER`. Returns 
    a list of analyzed forms. Word is None if `ANALYZER` failed
    to analyze it.

    Returns:
        list[str | None]: List of analyzed words(str) or failed words(None)
    """
    words = '\n'.join(words)
    analyzer = subprocess.Popen(["hfst-lookup", "-q", ANALYZER_FILE],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    res = analyzer.communicate(input=bytes(words, encoding='utf8'))[0].decode()
    analyzed = [x.split('\t')[1:] for x in res.split('\n\n') if x]
    return [None if x[1] == 'inf' else x[0]
            for x in analyzed]

BATCH_SIZE = 5_000
total = success = i = 0
words = []
def run():
    if not len(words): return
    global total, success, i
    analyzed = analyze(words)
    total += len(analyzed)
    success += sum(1 for x in analyzed if x)
    i += 1

for line in stdin:
    words.extend(line.strip().split())
    if len(words) < BATCH_SIZE:
        continue
    run()
    words.clear()

run()

print(f"Total:\t{total}\nPassed:\t{success}")
print(f"{success / total:.5f}")
