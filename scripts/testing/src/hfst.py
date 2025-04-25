from typing import List, Tuple, Union, Dict
from pathlib import Path
import subprocess

class HfstException(Exception):
    pass

class HFSTInvalidFormat(HfstException):
    pass

def parse_xerox(hfst_output: str) -> Dict[str, List[str]]:
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
    stdout, stderr, code = call_command(['hfst-lookup', '-q', '--output-format', 'xerox', hfst_file], 
                                        inp_str)
    if code != 0:
        raise HfstException(f'hfst-lookup: stdout={stdout}; stderr={stderr}')
    return stdout
