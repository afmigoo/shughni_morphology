from typing import List, Dict, Tuple, Union
from pathlib import Path
from .hfst import call_hfst_lookup, parse_xerox
import csv
import logging

from .TestCase import TestCase

logger = logging.getLogger(__name__)

def multiply_cases(cases: List[TestCase]) -> None:
    new_cases: List[TestCase] = []
    pairs = {
        'analyze': 'gen',
        'cyr2lat': 'lat2cyr'
    }
    pairs.update({v: k for k, v in pairs.items()})
    for c in cases:
        for substr in pairs.keys():
            if substr in c.fst:
                new_fst = c.fst.replace(substr, pairs[substr])
        new_cases.append(TestCase(input_str=c.output_str,
                                  output_str=c.input_str,
                                  origin_file=c.origin_file,
                                  fst=new_fst))
    cases.extend(new_cases)

def read_file(file: Path) -> List[TestCase]:
    contents: List[Tuple[str, str]] = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for line in reader:
            inp, out, mustpass, hfst_file = line[:4]
            if mustpass.lower() in ['pass', 'true']:
                contents.append(TestCase(input_str=inp.lower(), 
                                         output_str=out.lower(), 
                                         origin_file=file,
                                         fst=hfst_file))
    return contents

def eval_tests(files: List[Path], 
               hfst_root: Path, 
               do_multiply_cases: bool = True) -> Tuple[int, int, int]:
    # loading all test cases
    all_cases: List[TestCase] = []
    for f in files:
        all_cases.extend(read_file(f))
    logger.info(f'Loaded {len(all_cases)} test cases from {len(files)} files')

    # multiply cases, meaning reversing each case and feeding it to reversed fst
    if do_multiply_cases:
        multiply_cases(all_cases)
        logger.info(f'Multiplied cases, {len(all_cases)} cases in total')  
        
    # grouping by fst files
    fsts: Dict[str, List[TestCase]] = {}
    for case in all_cases:
        if case.fst in fsts:
            fsts[case.fst].append(case)
        else:
            fsts[case.fst] = [case]
    logger.info(f'{len(fsts)} FSTs tested')

    # calling fsts
    for fst, cases in fsts.items():
        fst_file = hfst_root.joinpath(f'{fst}.hfstol')
        if not fst_file.is_file():
            logger.error(f'FST doesn\'t exist: {fst_file}. Skipping {len(cases)} test cases')
            continue
        logger.info(f'Testing {fst}...')
        fst_output = parse_xerox(call_hfst_lookup(fst_file, [c.input_str for c in cases]))
        for c in cases:
            if not c.input_str in fst_output:
                logger.error(f'FST didn\'t return anything for {c.input_str}')
                c.passed = False
                continue
            c.check_pass(fst_output[c.input_str])

    total_passed = total_failed = 0
    for c in all_cases:
        if c.passed == True:
            total_passed += 1
        else:
            total_failed += 1
            logger.info(c)
    
    return total_passed, total_failed, len(all_cases)
