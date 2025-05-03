#!/usr/bin/env python3
from typing import List, Dict, Tuple, Callable, Union
from pathlib import Path
import csv
import sys
import re
import os
import argparse
import logging
from pprint import pformat
from tabulate import tabulate

from src.hfst import call_hfst_lookup, parse_apertium, ParsedItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--hfst-analyzer", required=True,
                    help="Hfst analyzer file that turns 'words' into 'word<n>><pl>'")
parser.add_argument("--csv", default='STDIN',
                    help="Csv file with pairs like 'words,word<n>><pl>'")
parser.add_argument("-p", "--pretty-output", action='store_true',
                    help="Print only total score with no file statistics.")
parser.add_argument("--drop-first-csv-row", action='store_true',
                    help="Csv file with pairs like 'words,word<n>><pl>'")
parser.add_argument("--hfst-translit",
                    help="Hfst transliterator to be applied to wordforms 'слово<n>' -> 'slovo<n>' if needed")
parser.add_argument("--details-dir",
                    help="Csv directory where details should be logged in format 'wordform,tagged,status'")

tag_aliases = {
    '<lat>': '<dat>'
}

AccFuncsMapping = Dict[str, Callable[[str, str], bool]]

def read_csv(file: Union[str, Path], drop_first = False) -> Tuple[List[str], List[str]]:
    if isinstance(file, str):
        file = Path(file)
    if not file.exists():
        raise FileNotFoundError(file)
    wordforms = []
    tagged = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        if drop_first:
            next(reader) # col names
        for w, t in reader:
            wordforms.append(w)
            tagged.append(t)
    assert len(wordforms) == len(tagged)
    return wordforms, tagged

def read_stdin(drop_first = False) -> Tuple[List[str], List[str]]:
    wordforms = []
    tagged = []
    reader = csv.reader(sys.stdin)
    if drop_first:
        next(reader) # col names
    for w, t in reader:
        wordforms.append(w)
        tagged.append(t)
    assert len(wordforms) == len(tagged)
    return wordforms, tagged

def get_stem(tagged: str) -> str:
    #                    prefixes     stem    suffixes
    return re.findall(r'(?:<[^<>]+>)*([^<>]+)(?:<[^<>]+>)*', tagged)[0]

def make_latin(items: List[ParsedItem], hfst: str):
    cyr2lat: Dict[str, List[str]] = {}
    # gathering all present stems
    for it in items:
        if '*' in it.out_variants[0]:
            continue
        for var in it.out_variants:
            stem = get_stem(var)
            cyr2lat[stem] = []
    # transliterating all stems at once is ~40 times faster than transliterating one stem at a time
    for translit in parse_apertium(call_hfst_lookup(hfst, list(cyr2lat.keys()))):
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

def match_exact(tagged1: str, tagged2: str) -> bool:
    return tagged1 == tagged2

def match_stem(tagged1: str, tagged2: str) -> bool:
    stem1 = get_stem(tagged1)
    stem2 = get_stem(tagged2)
    return stem1 == stem2

def match_pos(tagged1: str, tagged2: str) -> bool:
    pos_pattern = r'[^<>\n]+<([^<>]+)>'
    pos1 = re.findall(pos_pattern, tagged1)[0]
    pos2 = re.findall(pos_pattern, tagged2)[0]
    return pos1 == pos2

def match_stem_and_pos(tagged1: str, tagged2: str) -> bool:
    return match_stem(tagged1, tagged2) and match_pos(tagged1, tagged2)

def match_unordered(tagged1: str, tagged2: str) -> bool:
    tags1 = set(re.findall(r'<[^<>]+>', tagged1))
    tags2 = set(re.findall(r'<[^<>]+>', tagged2))
    return match_stem(tagged1, tagged2) and tags1 == tags2

def replace_aliases(tagged: List[str]):
    for i in range(len(tagged)):
        for old, new in tag_aliases.items():
            tagged[i] = tagged[i].replace(old, new)

def log_details(dir: Path, out_file: str, wordform: str, reference: str, real_output: str, result: str):
    if dir is None:
        return
    if not out_file.endswith('.csv'):
        out_file += '.csv'
    with open(dir.joinpath(out_file), 'a', encoding='utf-8') as out_f:
        writer = csv.writer(out_f)
        writer.writerow((wordform, reference, real_output, result))

def compare(reference: List[str], predicted: List[ParsedItem], 
            acc_funcs: AccFuncsMapping, details_dir: Path) -> dict:
    if len(reference) != len(predicted):
        raise RuntimeError(f'Reference count {len(reference)} != Predicted count {len(predicted)}')
    total = len(reference)
    recognized = 0
    acc_results = {k: {'correct': 0, 'recognized': 0} 
                   for k in acc_funcs.keys()}
    # evaluating absolute counts
    for ref, pred in zip(reference, predicted):
        is_correct = False
        if '*' in pred.out_variants[0]:
            log_details(details_dir, 'unknown', pred.input_str, ref, pred.variants(), 'UNKNOWN')
            continue
        recognized += 1
        for acc_type in acc_funcs.keys():
            acc_results[acc_type]['recognized'] += 1
            for pred_var in pred.out_variants:
                if acc_funcs[acc_type](ref, pred_var):
                    is_correct = True
                    acc_results[acc_type]['correct'] += 1
                    log_details(details_dir, acc_type, pred.input_str, ref, pred.variants(), 'CORRECT')
                    break
            if not is_correct:
                log_details(details_dir, acc_type, pred.input_str, ref, pred.variants(), 'FAIL')
    # evaluating fractional counts
    for acc_type in acc_funcs.keys():
        acc_results[acc_type]['acc'] = acc_results[acc_type]['correct'] /\
                                       acc_results[acc_type]['recognized']
    return {
        'total': total,
        'recognized': recognized,
        'accuracy': acc_results
    }

def main():
    args = parser.parse_args()
    details_dir = None
    if args.details_dir:
        details_dir = Path(args.details_dir)
        details_dir.mkdir(exist_ok=True, parents=True)
        for f in details_dir.iterdir():
            f.unlink()

    accuracy_funcs: AccFuncsMapping = {
        'exact_match':          match_exact,
        'stem_match':           match_stem,
        'pos_match':            match_pos,
        'stem_and_pos_match':   match_stem_and_pos,
        'unordered_tags_match': match_unordered,
    }
    if args.pretty_output:
        print('ELAN corpus')

    # READING THE DATA
    if args.csv == 'STDIN':
        wordforms, reference = read_stdin(drop_first=args.drop_first_csv_row)
    else:
        wordforms, reference = read_csv(args.csv, drop_first=args.drop_first_csv_row)
    # PREPROCESS
    replace_aliases(reference)
    predicted = parse_apertium(call_hfst_lookup(args.hfst_analyzer, wordforms))
    if args.hfst_translit:
        make_latin(predicted, hfst=args.hfst_translit)
    results = compare(reference, predicted, accuracy_funcs, details_dir=details_dir)
    if args.pretty_output:
        table = [['coverage', results['recognized']/results['total'], f"{results['recognized']}/{results['total']}"]]
        for metric, data in results['accuracy'].items():
            table.append([metric, data['acc'], f"{data['correct']}/{data['recognized']}"])
        for row in table:
            row[1] = f'{row[1] * 100:.2f}%'
        print(tabulate([['metric', 'value', 'absolute'], *table],
                        tablefmt="rounded_outline", headers='firstrow'))
        print()
    else:
        logger.info('{total} total; {rec} recognized; {cov:.4f} coverage\n{stats}'.format(
            total = results['total'], rec = results['recognized'],
            cov = results['recognized']/results['total'],
            stats = pformat({k: round(v['acc'], 3) for k, v in results['accuracy'].items()})
        ))

if __name__ == '__main__':
    main()
    #print(parse_apertium(call_hfst_lookup(HFST_ANALYZER, ['wi-rd-i', 'wi-rd-i', 'wi-rd-i'])))
