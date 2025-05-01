from typing import List, Tuple, Set
from pathlib import Path
import re

main_lexd = Path(__file__).parent.parent.parent.parent.joinpath('lexd/pron.lexd')

def get_pron_from_lexd(file: Path) -> Set[str]:
    pronouns = set()
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            if re.match(r'^[^ ]+:.*$', line):
                left_side = line.split(':')[0]
                pron = re.sub(r'<[^<>]+>', '', left_side)
                if pron:
                    pronouns.add(pron.strip())
    return pronouns

def fix_pronouns(lines: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    existing = get_pron_from_lexd(main_lexd)
    print(existing)
    return [l for l in lines if not l[0] in existing]