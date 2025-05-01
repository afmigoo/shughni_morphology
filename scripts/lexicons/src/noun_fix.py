from typing import Tuple, List

noun_plurals = {
    'pl_in-laws': ['свояк', 'своячн', 'зять', 'невестка', 'тесть', 'деверь', 'шурин', 'теща', 'свекровь'],
    'pl_cousins': ['двоюродный брат', 'двоюродная сестра'],
    'pl_sisters': ['сестра', 'сестричка'],
    'pl_timesOfDay': ['утро', 'утрен', 'день', 'дневн', 'вечер', 'ночь', 'ночн', 'сумерки', 'закат', 'восход'],
    'pl_timesOfYear': ['весна', 'зима', 'лето', 'осень'],
}

def fix_nouns(lines: List[Tuple[str, str]]):
    for i in range(len(lines)):
        for tag, triggers in noun_plurals.items():
            found = False
            for trig in triggers:
                if trig in lines[i][1]:
                    lines[i] = (f'{lines[i][0]}[{tag}]', lines[i][1])
                    found = True
                    break
            if found: 
                break
