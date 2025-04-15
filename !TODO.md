## 
- словообразование. что делать?

## Nouns
- Дополнить энклитики
- Дополнить суффиксы
- Дополнить префиксы
## Verbs
- Сделать ветку для образования прошедших от непрошедших форм? Там слошком много морфонологии
- Выражение гендера в основах глаголов
- Ресёрч что у глаголов есть ещё
## Тесты
- Заполнить тесты из литературы
    - Noun
    - Verb
    - Adj
    - other
- Transliteration tester 
    - ~~на словаре~~
    - на текстах

## SQLs
Extract all Shugni verbs
```sql
SELECT F.latin, F.cyrillic, M.meaning FROM Forms as F
JOIN Glosses as G ON G.gloss_id = F.gloss_id
JOIN Units as U ON U.unit_id = F.unit_id
JOIN Language_assignment as La ON La.unit_id = U.unit_id
JOIN Languages as L ON L.lang_id = La.lang_id
JOIN Meanings as M ON M.unit_id = F.unit_id
JOIN Parts_of_speech as POS ON POS.pos_id = M.pos_id
WHERE lang = 'шугнанский' AND G.gloss = 'inf' AND POS.pos = 'глагол'
```