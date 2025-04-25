#!/usr/bin/env python3
from typing import List, Dict, Tuple
from pathlib import Path
import csv
import re
import argparse
import logging
from tabulate import tabulate

from src.hfst import call_hfst_lookup, parse_apertium, ParsedItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--pretty-output", action='store_true',
                    help="Print only total score with no file statistics.")

csv_dir = Path(__file__).parent.joinpath('csv')
results = Path(__file__).parent.joinpath('results.csv')
results.unlink(missing_ok=True)
HFST_ANALYZER = Path(__file__).parent.parent.parent.joinpath('sgh_analyze_stem_word_lat.hfstol')
HFST_CYR2LAT = Path(__file__).parent.parent.parent.joinpath('translit/cyr2lat.hfstol')

tag_aliases = {
    '<lat>': '<dat>'
}

def read_csv(file: Path) -> Tuple[List[str], List[str]]:
    wordforms = []
    tagged = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        cols = next(reader) # col names
        if len(cols) != 2:
            raise RuntimeError(f'csv has !=2 cols: {len(cols)}')
        for w, t in reader:
            wordforms.append(w)
            tagged.append(t)
    assert len(wordforms) == len(tagged)
    return wordforms, tagged

def remove_morph_borders(items: List[ParsedItem]):
    for it in items:
        for i in range(len(it.out_variants)):
            it.out_variants[i] = it.out_variants[i].replace('>>', '>')

def get_stem(tagged: str) -> str:
    #                    prefixes     stem    suffixes
    return re.findall(r'(?:<[^<>]+>)*([^<>]+)(?:<[^<>]+>)*', tagged)[0]

def make_latin(items: List[ParsedItem]):
    cyr2lat: Dict[str, List[str]] = {}
    # gathering all present stems
    for it in items:
        if '*' in it.out_variants[0]:
            continue
        for var in it.out_variants:
            stem = get_stem(var)
            cyr2lat[stem] = []
    # transliterating all stems at once is ~40 times faster than transliterating one stem at a time
    for translit in parse_apertium(call_hfst_lookup(HFST_CYR2LAT, list(cyr2lat.keys()))):
        cyr2lat[translit.input_str] = translit.out_variants
    # replacing cyr stems with lat stems
    for it in items:
        if '*' in it.out_variants[0]:
            continue
        new_variants: List[str] = []
        for var in it.out_variants:
            stem = get_stem(var)
            for lat_stem in cyr2lat[stem]:
                new_variants.append(var.replace(stem, lat_stem))
        it.out_variants = new_variants

def is_identical(tagged1: str, tagged2: str) -> bool:
    tags1 = set(re.findall(r'<[^<>]+>', tagged1))
    tags2 = set(re.findall(r'<[^<>]+>', tagged2))
    stem1 = get_stem(tagged1)
    stem2 = get_stem(tagged2)
    return stem1 == stem2 and tags1 == tags2

def modernize_tags(tagged: List[str]):
    for i in range(len(tagged)):
        for old, new in tag_aliases.items():
            tagged[i] = tagged[i].replace(old, new)

def log_details(wordform: str, reference: str, real_output: str, result: str):
    with open(results, 'a', encoding='utf-8') as out_f:
        writer = csv.writer(out_f)
        writer.writerow((wordform, reference, real_output, result))

def compare(reference: List[str], predicted: List[ParsedItem]) -> Tuple[int, int, int]:
    "returns total, recognized, correct"
    if len(reference) != len(predicted):
        raise RuntimeError(f'Reference count {len(reference)} != Predicted count {len(predicted)}')
    total = len(reference)
    recognized = correct = 0
    for ref, pred in zip(reference, predicted):
        is_correct = False
        if '*' in pred.out_variants[0]:
            log_details(pred.input_str, ref, pred.variants(), 'UNKNOWN')
            continue
        recognized += 1
        for pred_var in pred.out_variants:
            if is_identical(ref, pred_var):
                is_correct = True
                log_details(pred.input_str, ref, pred.variants(), 'CORRECT')
                break
        if not is_correct:
            log_details(pred.input_str, ref, pred.variants(), 'FAIL')
        correct += int(is_correct)
    return total, recognized, correct

def main():
    args = parser.parse_args()
    csvs = [f for f in csv_dir.iterdir() if f.is_file() and f.name.endswith('.csv')]
    if args.pretty_output:
        print('ELAN corpus')
    
    glob_total = glob_rec = glob_correct = 0
    for file in csvs:
        wordforms, reference = read_csv(file)
        if len(wordforms) == 0:
            continue
        modernize_tags(reference)
        predicted = parse_apertium(call_hfst_lookup(HFST_ANALYZER, wordforms))
        remove_morph_borders(predicted)
        make_latin(predicted)
        total, rec, correct = compare(reference, predicted)
        if not args.pretty_output:
            logger.info(f'{correct/rec:.4f} accuracy; {rec/total:.4f} coverage; {total} total : {file.name}')
        glob_total += total
        glob_rec += rec
        glob_correct += correct

    if args.pretty_output:
        print(tabulate([['metric', 'value', 'absolute'],
                        ['coverage', f'{glob_rec/glob_total:.4f}', f'{glob_rec}/{glob_total}'],
                        ['accuracy', f'{glob_correct/glob_rec:.4f}', f'{glob_correct}/{glob_rec}']],
                        tablefmt="rounded_outline", headers='firstrow'))
        print()
    else:
        logger.info(f'TOTAL : {glob_correct/glob_rec:.4f} accuracy; {glob_rec/glob_total:.4f} coverage; {glob_total} total tokens')

if __name__ == '__main__':
    main()
    #print(parse_apertium(call_hfst_lookup(HFST_ANALYZER, ['wi-rd-i', 'wi-rd-i', 'wi-rd-i'])))
