# PUBLISH2 — pochodzenie i otwarte prawa / provenance and open rights

Status **OPEN**. Prywatny push/Draft jest dozwolony przez właściciela;
nie oznacza prawa do publicznej dystrybucji. Istniejące MIT, CC BY-NC-SA,
cc65 i Void Strike notices pozostają zachowane. Nie zastąpiono muzyki ani map.

## Service Current

Bieżący generator: `experiments/eng3-observed-input-3pal/compile.py`, funkcja
generująca patterny/instrumenty i `music.json` (tytuł Service Current, CC0-1.0),
odtwarzacz w `hardware.s`, wynik `music.nrq` (1552 B body). Historia śledzi
rodzinę generatora i `LICENSE-music.md` do `dea2fe55676fa475ad8bf1f29f61112d635084d2`
(„checkpoint: qualify A3 latency and obstacle candidate (FAIL)”).
Historyczny notice `experiments/renderer-a3/LICENSE-music.md` mówi o nowej
kompozycji, ośmiu 64-wierszowych patternach, trzech kanałach i 16 częściach;
deklaruje CC0 dla kompozycji/instrumentów i MIT dla playera. Późniejsze
renderer-a4/a5 utrzymują notice. Bieżący generator podaje te same parametry,
nie importuje sampli ani gotowego zewnętrznego utworu. To dowód konstrukcji
i ciągłości deklaracji, a nie tożsamości uprawnionego autora. Nazwa autora
commitu „Atari Sokoban Dev” i placeholder e-mail nie są dowodem praw.

Potrzeba: oświadczenie osoby uprawnionej wskazujące kompozycję i instrumenty,
pochodzenie oraz upoważnienie do historycznego CC0; albo dokument źródłowy
potwierdzający te prawa. Jeżeli CC0 był skuteczny, trzeba zachować go jako
wyjątek od nowej licencji NC-SA. Sam LICENSE nie odwołuje wcześniejszego CC0.

## Odziedziczone mapy / inherited map fixtures

Pierwszy dostępny checkpoint `8056a70` już zawiera te układy. Jego opis mówi
o zachowaniu odziedziczonego silnika i audycie pochodzenia; wcześniejszej
historii tworzenia map nie znaleziono w tym repo. Pliki:

- `tools/levels_final.py`: źródłowa lista 20 układów, deklaracja „20 original”
  jest tekstem źródła, nie niezależnym dowodem autorstwa.
- `src/levels_data.c`: wygenerowane z tej listy 20 map `l1`–`l20`.
- `assets/levels/prototypes.json`: FIRST DOCK = mapa 1 „Pierwszy krok”;
  REACTOR STORE = mapa 14 „Piatka”. Metadane jawnie wskazują dziedziczenie
  i niezmienioną zagadkę. FOUNDRY BAY jest opisana jako własny stress fixture.
- `experiments/eng3-observed-input-3pal/reference/prototype_assets.c`:
  wygenerowane kopie fixture'ów używane w zamrożonych wejściach kompilacji.

20 nazw: Pierwszy krok; Za rog; Dwa pudelka; Wybor drogi; Kolejnosc ma
znaczenie; Ciasny magazyn; Trzy skrzynie; Rozstaw; Slepy zaulek; Filar;
Cztery katy; Wnetrze; Podwojny zamek; Piatka; Waskie mosty; Kwadrat;
Rozgalezienie; Sciezka wojownika; Ostatnia komnata; Mistrz Sokoban.

Potrzeba: autor i pierwotne źródło tych konkretnych 20 układów oraz zgoda/
licencja pozwalająca rozpowszechniać je i ich adaptacje w repozytorium. Jeśli
właściciel stworzył je sam, potrzebne jest jednoznaczne oświadczenie wskazujące
listę i pliki; nazwy, prostota mapy ani wpisanie jej do repo nie wystarczają.

Końcowa kampania `assets/levels/camp2-b/campaign.json` zachowana bajtowo
(`131c57e2692ffe121392e1260c13060960ac8f54425dd870dea28114cd6dae39`).
Metadane deklarują 46 nowych i 14 zachowanych układów projektu. Porównanie
kanoniczne wszystkich 60 z powyższymi 20, narzędziem `product1_campaign.canonical`,
nie znalazło równych układów; nie jest to globalny dowód oryginalności.
Otwarte zastrzeżenie odziedziczonych fixture'ów dotyczy źródeł eksportu,
a nie podmiany finalnych sektorów NSLV.

## Bitmapa referencyjna

`reference/vis1-owner/energy-owner-reference.png` pozostaje lokalnie,
bez zmian i poza eksportem. Nie jest wejściem ATR. Do jej ewentualnej
redystrybucji potrzeba oryginalnego źródła i zgody uprawnionego. Zdjęcia
sprzętowe opisane przez właściciela nie były dostarczone jako pliki w tej
sesji; raport opiera się na jego opisie, nie deklaruje inspekcji tych zdjęć.

## English

Rights remain OPEN. Repository history establishes when the procedural
Service Current generator/CC0 notice and 20 inherited map fixtures entered
this repository; commit metadata alone does not establish authorized authorship.
Required: an authorized statement or original licence/provenance for the named
composition/instruments and all 20 named historical layouts, particularly
FIRST DOCK (1) and REACTOR STORE (14). Preserve any valid CC0 grant. The final
60-map campaign is unchanged; canonical equality with those 20 found no matches,
which is a limited comparison, not proof of global originality. Owner reference
bitmap remains excluded pending redistribution permission. Existing component
notices and attribution stay intact. No stable publication until these decisions
and actual Atari acceptance are complete.
