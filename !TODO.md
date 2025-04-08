## Русские леммы
- scripts/ru_lemmas 
- доделать чтобы он распознавал не только основа<тэг>:лемма<тэг>, но и любое кол-во тэгов после 
- попробовать присоединить через hfst-compose к выводу анализаторов (+ вводу генераторов?)

## Переезд на новый формат!
- Сделать основной генератор формата `stem<tag><tag> -> stem>morph>morph`
    - Убедиться что анализатиор корректно разворачивается с учётом нового формата
- Сделать вторую версию пары генератор/анализатор БЕЗ разделителей, т.е. `stem<tag><tag> -> stemmorphmorph`
    - Убедиться что анализатиор корректно разворачивается с учётом нового формата
- Убедиться в сочетаемости с транслитераторами
- Что делать со словами, у которых дефис в основе? Эти дефисы теряются в `sgh_*_morph_*/hfst` файлах
## Nouns
- Дополнить энклитики
- Дополнить суффиксы
- Дополнить префиксы
## Verbs
- Сделать ветку для образования прошедших от непрошедших форм? Там слошком много морфонологии
- Выражение гендера в основах глаголов
- Ресёрч что у глаголов есть ещё
## Тесты
- Подумать писать ли питоновский скрипт тестер или писать csv тесты под каждый .hfst файл отдельно
- Transliteration tester

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