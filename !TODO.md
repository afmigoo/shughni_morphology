## 
- словообразование. что делать?
- добавить '=' перед клитиками?
- послелоги

## Nouns
- Дополнить энклитики
- Дополнить суффиксы
- Дополнить префиксы
## Verbs
- Выражение гендера в основах глаголов
- Расширить варианты глагольных основ из БД (напр. Gloss pst.sh)
- ДОБАВИТЬ остальные глагольные основы из БД (npst.3sg etc)
## Adjectives
- Отглагольные прилагательные (participle): решить делать ли один тег (PTCP) или два (PTCP1, PTCP2)
- compound adjectives (adj + n) 
    - делать ли фонологию озвончения (Parker p. 175) если она непродуктивна и уже учтена в словаре скоере всего?
    - могут ли PTCP или отименные прилагательные занимать место adj в компаундах?
## Pronouns

## Тесты
- Transliteration tester 
    - ~~на словаре~~
    - на текстах
## Metrics
- Accuracy
    - считать accuracy если разбор fst совпал хотябы с одним разбором этого токена включая другие контексты(?)

## SQLs
Extract all POS
```sql
SELECT F.cyrillic, M.meaning FROM Forms as F
JOIN Glosses as G ON G.gloss_id = F.gloss_id
JOIN Units as U ON U.unit_id = F.unit_id
JOIN Language_assignment as La ON La.unit_id = U.unit_id
JOIN Languages as L ON L.lang_id = La.lang_id
JOIN Meanings as M ON M.unit_id = F.unit_id
JOIN Parts_of_speech as POS ON POS.pos_id = M.pos_id
WHERE lang = 'шугнанский' AND POS.pos = 'существительное' AND 
	NOT (F.cyrillic LIKE '-%' OR F.cyrillic LIKE '%-')
```