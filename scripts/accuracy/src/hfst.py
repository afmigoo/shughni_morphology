from typing import List, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
import subprocess
import re

class HfstException(Exception):
    pass

class HFSTInvalidFormat(HfstException):
    pass

@dataclass
class ParsedItem:
    input_str: str
    out_variants: List[str]

    def variants(self) -> str:
        return f'{"/".join(self.out_variants)}'

    def __str__(self):
        return f'{self.input_str} -> {self.variants()}'

    def __repr__(self):
        return f'[ParsedItem {str(self)}]'

def call_command(args: List[str], input: str) -> Tuple[str, str, int]:
    """Call custom bash command and pass input to stdin

    Parameters
    ----------
    args : List[str]
        args that will be passed to Popen. example: ['hfst-lookup', '-q', 'english.hfst']
    input : str
        input that will be passed to stdin

    Returns
    -------
    Tuple[str, str, int]
        stdout, stderr and return code
    """
    proc = subprocess.Popen(args,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate(input=bytes(input, encoding='utf-8'))
    stdout = stdout.decode() if stdout else ''
    stderr = stderr.decode() if stderr else ''
    return stdout, stderr, proc.returncode

def call_hfst_lookup(hfst_file: Union[Path, str],
                     input_strings: List[str]) -> str:
    if isinstance(hfst_file, str):
        hfst_file = Path(hfst_file)
    if not hfst_file.is_file():
        raise FileNotFoundError(hfst_file)

    inp_str = '\n'.join(input_strings)
    stdout, stderr, code = call_command(['hfst-lookup', '-q', '--output-format', 'apertium', hfst_file], 
                                        inp_str)
    if code != 0:
        raise HfstException(f'hfst-lookup: stdout={stdout}; stderr={stderr}')
    return stdout

def parse_apertium(stdout: str) -> List[ParsedItem]:
    items: List[ParsedItem] = []
    # regex: all strings like '^+$' (apertium format) with no nested ^ or $ 
    for raw in re.finditer(r'\^([^\^\$]+)\$', stdout):
        apertium = raw.groups()[-1]
        input_str, *output_variants = apertium.split('/')
        items.append(ParsedItem(input_str=input_str,
                                out_variants=output_variants))
    return items
