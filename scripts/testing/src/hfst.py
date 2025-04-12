from typing import List, Tuple, Union, Dict
from pathlib import Path
import subprocess

def parse_output(hfst_output: str) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    output_strings = hfst_output.split('\n\n')
    output_strings = [s for s in output_strings if not s == '']

    for s in output_strings:
        # a\tA\t0.0\na\tB\t0.0 -> [[a, A], [a, B]]
        variants = [x.split('\t')[:2] for x in s.split('\n')]
        assert all(x[0] == variants[0][0] for x in variants)
        input_string = variants[0][0]
        # [[a, A], [a, B]] -> [A, B]
        variants = [x[1] for x in variants]
        result[input_string] = variants
    
    return result

def call_hfst(hfst_file: Union[Path, str], 
              input_strings: List[str]) -> Dict[str, List[str]]:
    """Inputs all strings to a HFST transducer and returns it's output.

    Args:
        input_strings (List[str]): list of input strings

    Returns:
        List[tuple]: list of string pairs (input, output)
    """
    if isinstance(hfst_file, str):
        hfst_file = Path(hfst_file)
    if not hfst_file.is_file():
        raise FileNotFoundError(hfst_file)
    
    inp_str = '\n'.join(input_strings)
    translit = subprocess.Popen(["hfst-lookup", "-q", hfst_file],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    res = translit.communicate(input=bytes(inp_str, encoding='utf8'))[0].decode()

    return parse_output(res)
