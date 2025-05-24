## 
- словообразование. что делать?
- добавить '=' перед клитиками?
- послелоги

## Nouns
- Дополнить энклитики
- Дополнить суффиксы
- Дополнить префиксы
## Verbs
- PAST INFLECTION CLITICS (Parker 262)
- INF2 + IMPER регулярным образом от других глагольных основ (Меленченко)
- Выражение гендера в основах глаголов
- Расширить варианты глагольных основ из БД (напр. Gloss pst.sh)
- ДОБАВИТЬ остальные глагольные основы из БД (npst.3sg etc)
## Adjectives
- Отглагольные прилагательные (participle): решить делать ли один тег (PTCP) или два (PTCP1, PTCP2)
- compound adjectives (adj + n) 
    - делать ли фонологию озвончения (Parker p. 175) если она непродуктивна и уже учтена в словаре скоере всего?
    - могут ли PTCP или отименные прилагательные занимать место adj в компаундах?
## Pronouns
- локатив и датив в суффиксах местоимений могут быть также глобальными клитиками у всех остальных единиц речи (source: глоссы максима)

## Тесты
- Transliteration tester 
    - ~~на словаре~~
    - на текстах
## Metrics
- Accuracy
    - считать accuracy если разбор fst совпал хотябы с одним разбором этого токена включая другие контексты(?)
    - CNJ CONJ alias

## Translit
- почему stress удаляется только lat2cyr 

## POS
- ~~глагол~~
- ~~существительное~~
- ~~прилагательное~~
- ~~местоимение~~
- междометие
- наречие
- причастие
- ~~числительное~~
- частица
- ~~предлог~~
- послелог
- ~~союз~~
- вводное слово
- предикатив

## Glosses!!!
- sup.pl
- ~~pst.sh~~
- ~~pst.m~~
- ~~pst.f/pl~~
- ~~pst.f~~
- ~~pst~~
- proh.sh
- proh
- ~~pf.pl~~
- ~~pf.m~~
- ~~pf.f~~
- ~~pf~~
- ~~npst.sh~~
- ~~npst.f.3sg~~
- ~~npst.f~~
- ~~npst.3sg.sh~~
- ~~npst.3sg~~
- ~~npst.3pl.sh~~
- ~~npst.3pl~~
- ~~npst.2sg.sh~~
- ~~npst.2sg~~
- ~~npst.2pl.sh~~
- ~~npst.2pl~~
- ~~npst.1sg.sh~~
- ~~npst.1sg~~
- ~~npst.1pl~~
- ~~npst~~
- ~~noun.pl~~
- ~~inf.sh~~
- ~~inf.f~~
- ~~inf~~
- ~~imper.sh~~
- ~~imper~~
- dim
- cv
- comp

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