from src.evaluate import eval_tests
from pathlib import Path
import argparse
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--multiply-cases", action='store_true',
                    help="Multiply test cases by inverting them \
                          and feeding to inverted FST, by transliterating \
                          and feeding to different script fst")

tests_root = Path(__file__).parent.joinpath('tests')
hfst_root = Path(__file__).parent.parent.parent
if not tests_root.is_dir():
    raise FileNotFoundError(f'Directory {tests_root} is missing')

def main():
    args = parser.parse_args()

    morph_files = [
        tests_root.joinpath('adj.csv'),
        tests_root.joinpath('conj.csv'),
        tests_root.joinpath('lat.csv'),
        tests_root.joinpath('noun.csv'),
        tests_root.joinpath('num.csv'),
        tests_root.joinpath('pron.csv'),
        tests_root.joinpath('verb.csv'),
    ]
    translit_files = [
        tests_root.joinpath('translit.csv')
    ]

    t_passed, t_failed, t_total = eval_tests(translit_files, hfst_root, do_multiply_cases=args.multiply_cases)
    m_passed, m_failed, m_total = eval_tests(morph_files, hfst_root, do_multiply_cases=args.multiply_cases)

    logger.info(f'Transliteration: {t_passed} ({100*t_passed/t_total:.2f}%) passed; {t_failed} failed; {t_total} total')
    logger.info(f'Morphology: {m_passed} ({100*m_passed/m_total:.2f}%) passed; {m_failed} failed; {m_total} total')

if __name__ == '__main__':
    start = time.time()
    main()
    logger.info(f'Testing done in {time.time() - start:.3f}sec')
