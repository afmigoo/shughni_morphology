from typing import List, Tuple
import re

def rep1(verb_stem: str) -> str:
    return re.sub(r'[тд](\[.\])?$', '\g<1>', verb_stem)

def replace_ending_td(lines: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    return [(rep1(l[0]), l[1]) for l in lines]

def rep2(verb_stem: str) -> str:
    return re.sub(r'[чҷ](\[.\])?$', '\g<1>', verb_stem)

def replace_ending_ch(lines: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    return [(rep2(l[0]), l[1]) for l in lines]
