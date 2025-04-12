from typing import List, Dict, Tuple, Union
from pathlib import Path
from .hfst import call_hfst
import csv
from pprint import pprint
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    input_str: str
    output_str: str
    origin_file: Path
    fst: str
    passed: bool = None
    real_output: List[str] = None

    def check_pass(self, real_output: List[str]) -> bool:
        self.real_output = real_output
        self.passed = self.output_str in self.real_output
        return self.passed

    def __str__(self):
        status = 'Unkn ?'
        if self.passed == True:
            status = 'Pass ✅' 
        elif self.passed == False:
            status = 'Fail ❌'
        comment = ''
        if self.real_output:
            comment = f" (fst output: {'|'.join(self.real_output)})"
        
        return f'{status} [{self.origin_file.name}:{self.fst}] {self.input_str}:{self.output_str}{comment}'

def multiply_cases(cases: List[TestCase]) -> None:
    new_cases: List[TestCase] = []
    for c in cases:
        old_prefix = c.fst.split('_')[0]
        if old_prefix == 'analyze':
            new_prefix = 'gen'
        elif old_prefix == 'gen':
            new_prefix = 'analyze'
        new_cases.append(TestCase(input_str=c.output_str,
                                output_str=c.input_str,
                                origin_file=c.origin_file,
                                fst=c.fst.replace(old_prefix, new_prefix)))
    cases.extend(new_cases)

def read_file(file: Path) -> List[TestCase]:
    contents: List[Tuple[str, str]] = []
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for line in reader:
            inp, out, mustpass, hfst_file = line[:4]
            if mustpass.lower() in ['pass', 'true']:
                contents.append(TestCase(input_str=inp, 
                                         output_str=out, 
                                         origin_file=file,
                                         fst=hfst_file))
    return contents

def morph_test(files: List[Path], 
               hfst_root: Path, 
               do_multiply_cases: bool = True):
    # loading all test cases
    all_cases: List[TestCase] = []
    for f in files:
        all_cases.extend(read_file(f))
    logger.info(f'Loaded {len(all_cases)} test cases from {len(files)} files')

    # multiply cases, meaning reversing each case and feeding it to reversed fst
    if do_multiply_cases:
        multiply_cases(all_cases)
        logger.info(f'Multiplied cases. {len(all_cases)} cases total')  
        
    # grouping by fst files
    fsts: Dict[str, List[TestCase]] = {}
    for case in all_cases:
        if case.fst in fsts:
            fsts[case.fst].append(case)
        else:
            fsts[case.fst] = [case]
    logger.info(f'FSTs tested: {" ".join(fsts.keys())}')

    # calling fsts
    for fst, cases in fsts.items():
        fst_file = hfst_root.joinpath(f'{fst}.hfst')
        if not fst_file.is_file():
            logger.error(f'FST doesn\'t exist: {fst_file}. Skipping {len(cases)} test cases')
            continue
        logger.info(f'Testing {fst}...')
        fst_output = call_hfst(fst_file, [c.input_str for c in cases])
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
    
    logger.info(f'{total_passed} passed; {total_failed} failed; {len(all_cases)} total')