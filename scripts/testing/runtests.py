from src.morph_test import morph_test, read_file
from pathlib import Path
from pprint import pprint

import logging

logging.basicConfig(level=logging.INFO)

tests_root = Path(__file__).parent.joinpath('tests')
hfst_root = Path(__file__).parent.parent.parent

if not tests_root.is_dir():
    raise FileNotFoundError(f'Directory {tests_root} is missing')

def main():
    morph_files = [
        tests_root.joinpath('lat.csv'),
        tests_root.joinpath('noun.csv'),
        tests_root.joinpath('num.csv'),
        tests_root.joinpath('verb.csv'),
    ]
    morph_test(morph_files, hfst_root, do_multiply_cases=False)

if __name__ == '__main__':
    main()
