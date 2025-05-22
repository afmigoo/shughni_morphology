#!/usr/bin/env python3
from typing import List, Dict, Tuple, Callable, Union, Literal, Set, Iterable
from collections import defaultdict
from dataclasses import dataclass
from pprint import pprint
from pathlib import Path
import subprocess
import argparse
import logging
import csv
import sys
import re
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

desc="""This script evaluates .hfst/.hfstol coverage and accuracy on csv-like corpus. By default it reads corpus from stdin.

The input corpus lines must contain a single token and have format 'hfst_in,hfst_out'. The script will stream `hfst_in` column into provided --hfst-analyzer and evaluate accuracy.
Line is considered to pass accuracy score if AT LEAST ONE of --hfst-analyzer outputs matches `hfst_out` value.

In code's 'Custom accuracy functions' block you can add your own accuracy functions.
Function must have typing `(str, str) -> bool`, where strings are like 'car<n>><pl>','car<n>><sg>'.
Don't forget to add your function to global `accuracy_funcs` dict.
"""

parser = argparse.ArgumentParser(description=desc,
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="Author: Kartina Elen @ HSE University 2025")
parser_required = parser.add_argument_group('required')
parser_required.add_argument('-H', '--hfst-analyzer', required=True,
    help='Hfst analyzer file that turns \'words\' into \'word<n>><pl>\'')
parser_optional = parser.add_argument_group('optional')
parser_optional.add_argument('-i', '--csv', default='STDIN',
    help='Csv file with pairs like \'words,word<n>><pl>\'. Set to \'STDIN\' to read csv from stdin. Default: \'STDIN\'')
parser_optional.add_argument('-f', '--output-format', default='table',
                             choices=['table', 'json', 'json_indent'],
    help='Metrics print format. \'table\'=pretty human-readable. Default is \'table\'')
parser_optional.add_argument('--drop-first-csv-row', action='store_true',
                             help='Ignore the first line from the --csv input. Useful for csv\'s with column names.')
parser_optional.add_argument('--hfst-translit',
    help='Hfst transliterator to be applied to --hfst-analyzer\'s output stems \'слово<n>\' -> \'slovo<n>\' if needed')
parser_optional.add_argument('--details-dir',
    help='Csv directory where details should be logged in format \'wordform,tagged,status\'')

tag_aliases = {
    '<lat>': '<dat>',
    '<o>': '<obl>'
}

EqFunc = Callable[[str, str], bool]

###############
#    INPUT    #
###############
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

###############
#    HFST     #
###############
class HfstException(Exception):
    pass

@dataclass
class ParsedItem:
    input_str: str
    out_variants: List[str] | None

    def variants(self) -> str:
        return f'{"/".join(self.out_variants)}' if self.out_variants else 'UNK'
    def __str__(self):
        return f'{self.input_str} -> {self.variants()}'
    def __repr__(self):
        return f'[ParsedItem {str(self)}]'

def parse_apertium(stdout: str) -> List[ParsedItem]:
    items: List[ParsedItem] = []
    # regex: all strings like '^+$' (apertium format) with no nested ^ or $ 
    for raw in re.finditer(r'\^([^\^\$]+)\$', stdout):
        apertium = raw.groups()[-1]
        input_str, *output_variants = apertium.split('/')
        if '*' in output_variants[0]: # unrecognized
            output_variants = None
        else:
            # leaving only unique strings
            output_variants = sorted(set(output_variants))
        items.append(ParsedItem(input_str=input_str,
                                out_variants=output_variants))
    return items

def hfst_lookup(hfst_file: Union[Path, str],
                input_strings: List[str]) -> List[ParsedItem]:
    if isinstance(hfst_file, str):
        hfst_file = Path(hfst_file)
    if not hfst_file.is_file():
        raise FileNotFoundError(hfst_file)
    proc = subprocess.Popen(['hfst-lookup', '-q', '--output-format', 'apertium', hfst_file],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate(input=bytes('\n'.join(input_strings), 
                                      encoding='utf-8'))
    stdout = stdout.decode() if stdout else ''
    stderr = stderr.decode() if stderr else ''
    if proc.returncode != 0:
        raise HfstException(f'hfst-lookup: stdout={stdout}; stderr={stderr}')
    parsed = parse_apertium(stdout)
    assert set(x.input_str for x in parsed) == set(input_strings)
    return parsed

##############################
#    Stem Transliteration    #
##############################
def get_stem(tagged: str) -> str:
    return re.findall(r'>?([^<>]+)<', tagged)[0]

def make_latin(items: List[ParsedItem], hfst: str):
    cyr2lat: Dict[str, List[str]] = {}
    # gathering all present stems
    for it in items:
        if it.out_variants is None:
            continue
        for var in it.out_variants:
            stem = get_stem(var)
            cyr2lat[stem] = []
    # transliterating all stems at once is ~40 times faster than transliterating one stem at a time
    for translit in hfst_lookup(hfst, list(cyr2lat.keys())):
        if not translit.out_variants is None:
            cyr2lat[translit.input_str] = translit.out_variants
    # replacing cyr stems with lat stems
    for it in items:
        if it.out_variants is None:
            continue
        new_variants: List[str] = []
        for var in it.out_variants:
            stem = get_stem(var)
            for lat_stem in cyr2lat[stem]:
                new_variants.append(var.replace(stem, lat_stem))
        it.out_variants = new_variants

###################################
#    Custom accuracy functions    #
###################################
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

accuracy_funcs: Dict[str, EqFunc] = {
    'exact_match':          match_exact,
    'stem_match':           match_stem,
    'pos_match':            match_pos,
    'stem_and_pos_match':   match_stem_and_pos,
    'unordered_tags_match': match_unordered,
}
################
#    OUTPUT    #
################
def log_details(dir: Path, out_file: str, 
                wordform: str, reference: str,
                real_output: str, result: str):
    if dir is None:
        return
    if not out_file.endswith('.csv'):
        out_file += '.csv'
    with open(dir.joinpath(out_file), 'a', encoding='utf-8') as out_f:
        writer = csv.writer(out_f)
        writer.writerow((wordform, reference, real_output, result))

def table_results(results: dict):
    print(tabulate([['metric', 'Value', 'Absolute'],
                    ['coverage', results['recognized']/results['total'], f"{results['recognized']}/{results['total']}"]],
                    tablefmt="rounded_outline", headers='firstrow'))
    columns = list(next(iter(results['metrics'].values())).keys()) # BRUH
    columns.sort()
    table = []
    for metric, data in results['metrics'].items():
        table.append([metric, *[data[c] for c in columns]])
    print(tabulate([['metric', *columns], *table],
                    tablefmt="rounded_outline", headers='firstrow'))
    print()

####################
#    Evaluation    #
####################
def replace_aliases(wf_variants: Dict[str, List[str]]):
    for wf, variants in wf_variants.items():
        for i in range(len(variants)):
            for old, new in tag_aliases.items():
                variants[i] = variants[i].replace(old, new)

def count_tp_fn_fp(gold_standard: List[str], fst_output: List[str], 
                   eq_fn: EqFunc) -> Tuple[int, int, int]:
    TP = 0
    gold_missing = [True] * len(gold_standard)
    fst_missing = [True] * len(fst_output)
    for i in range(len(gold_standard)):
        for j in range(len(fst_output)):
            if eq_fn(gold_standard[i], fst_output[j]):
                TP += 1
                gold_missing[i] = fst_missing[j] = False
    FN = sum(int(flag) for flag in gold_missing)
    FP = sum(int(flag) for flag in fst_missing)
    return TP, FN, FP

def compare(ref_variants: Dict[str, List[str]], predicted: List[ParsedItem], 
            acc_funcs: Dict[str, EqFunc], details_dir: Path) -> dict:
    details_dir.mkdir(exist_ok=True, parents=True)
    for f in details_dir.iterdir():
        f.unlink()
    total = len(predicted)
    recognized = 0
    raw_metrics = {k: {'TP': 0, 'FN': 0, 'FP': 0, 'ANY': 0}
                   for k in acc_funcs.keys()}
    # evaluating absolute TP, FN, FP counts
    for pred in predicted:
        if not pred.input_str in ref_variants:
            raise RuntimeError(f'Prediction {pred} is missing in gold standard')
        reference_variants = '/'.join(ref_variants[pred.input_str])
        if pred.out_variants is None:
            log_details(details_dir, 'unknown', pred.input_str, reference_variants, pred.variants(), 'UNKNOWN')
            continue
        recognized += 1
        for acc_variant in acc_funcs.keys():
            TP, FN, FP = count_tp_fn_fp(ref_variants[pred.input_str], pred.out_variants, 
                                        acc_funcs[acc_variant])
            log_details(details_dir, acc_variant, pred.input_str, 
                        reference_variants, pred.variants(), 
                        f'TP={TP};FN={FN};FP={FP}')
            raw_metrics[acc_variant]['TP'] += TP
            raw_metrics[acc_variant]['FN'] += FN
            raw_metrics[acc_variant]['FP'] += FP
            raw_metrics[acc_variant]['ANY'] += int(TP > 0)
    # evaluating Precision and Recall
    FP = total - recognized # FP = unrecognized
    for acc_variant in acc_funcs.keys():
        FN = raw_metrics[acc_variant].pop('FN')
        TP = raw_metrics[acc_variant].pop('TP')
        FP = raw_metrics[acc_variant].pop('FP')
        raw_metrics[acc_variant]['Precision'] = TP / (TP + FP)
        raw_metrics[acc_variant]['Recall'] = TP / (TP + FN)
    # evaluating lazy accuracy
    for acc_variant in acc_funcs.keys():
        if recognized == 0:
            raw_metrics[acc_variant]['Accuracy(any)'] = 0
        else:
            raw_metrics[acc_variant]['Accuracy(any)'] = raw_metrics[acc_variant].pop('ANY') / recognized
    return {
        'total': total,
        'recognized': recognized,
        'metrics': raw_metrics
    }

def main():
    args = parser.parse_args()
    details_dir = None
    if args.details_dir:
        details_dir = Path(args.details_dir)
        all_subdir = details_dir.joinpath('all')
        unique_subdir = details_dir.joinpath('unique_subdir')

    # READING THE DATA
    if args.csv == 'STDIN':
        wordforms, reference = read_stdin(drop_first=args.drop_first_csv_row)
    else:
        wordforms, reference = read_csv(args.csv, drop_first=args.drop_first_csv_row)
    # Forming all unique reference variants for all unique wordforms
    wf_variants = defaultdict(list)
    wf_freq = defaultdict(int)
    for wf, ref in zip(wordforms, reference):
        if not ref in wf_variants[wf]:
            wf_variants[wf].append(ref)
        wf_freq[wf] += 1
    # PREPROCESS
    replace_aliases(wf_variants)
    # PREDICTION
    predicted_unique = hfst_lookup(args.hfst_analyzer, list(wf_variants.keys()))
    predicted_all = hfst_lookup(args.hfst_analyzer, wordforms)
    if args.hfst_translit:
        make_latin(predicted_unique, hfst=args.hfst_translit)
        make_latin(predicted_all, hfst=args.hfst_translit)
    # EVALUATE
    results_unique = compare(wf_variants, predicted_unique, accuracy_funcs, details_dir=unique_subdir)
    results_all = compare(wf_variants, predicted_all, accuracy_funcs, details_dir=all_subdir)
    # PRINT
    if args.output_format == 'table':
        print('All tokens')
        table_results(results_all)
        print('Unique tokens')
        table_results(results_unique)
    else:
        json_ = {'all': results_all, 'unique': results_unique}
        if args.output_format == 'json':
            print(json_)
        if args.output_format == 'json_indent':
            pprint(json_)

if __name__ == '__main__':
    main()
    #count_tp_fn_fp(['a<n>', 'a<conj>'], ['a<n>', 'a<v>', 'a<adj>'], match_stem_and_pos)
