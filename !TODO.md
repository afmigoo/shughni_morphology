## 
- словообразование. что делать?
- добавить '=' перед клитиками?
- ОБНОВИТЬ ДАМПЫ лексоконов из новой версии бд

## Nouns
- Дополнить энклитики
- Дополнить суффиксы
- Дополнить префиксы
- Удалить '-' с хвостов в новом дампе
## Verbs
- Сделать ветку для образования прошедших от непрошедших форм? Там слошком много морфонологии
- Выражение гендера в основах глаголов
- Расширить варианты глагольных основ из БД (напр. Gloss pst.sh)
- Что делать с подобными фейлами в accuracy? `lůd,lů<v><pst>,lůd<v><imp>,FAIL`
## Adjectives
- Префиксные адективаторы: что делать с глоссами типа `<with>`
- Отглагольные прилагательные (participle): решить делать ли один тег (PTCP) или два (PTCP1, PTCP2)
- compound adjectives (adj + n) 
    - делать ли фонологию озвончения (Parker p. 175) если она непродуктивна и уже учтена в словаре скоере всего?
    - могут ли PTCP или отименные прилагательные занимать место adj в компаундах?
## Тесты
- Заполнить тесты из литературы
    - Noun
    - Verb
    - Adj
    - other
- Transliteration tester 
    - ~~на словаре~~
    - на текстах
## Rulem
- пофиксить пустые леммы (штук 30)
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