# HWVIS1 + PUBLISH2 — NEON SHIFT 65 1.0, OWNER_PENDING

Kandydat: checkpoint źródłowy `a9448bfb887fd4a2c35182cb8a54a4ea2cb7a1ea`.
Normalny ATR SHA-256:
`48b6f81986d8ffb705830aa7f2dfffdb4419b3508a8409be006210441bac8c7d`.
Stan: kwalifikacja emulatora opisana niżej; **Atari/SIO2SD, wygląd i odsłuch:
OWNER_PENDING; prawa OPEN**. Brak stabilnej publikacji i finalnego tagu v1.0.0.

## Diagnoza

Stan wejściowy: lokalny branch chore/publish1, HEAD `154560d`; zdalne
Setech-pl/neon-shift-65 prywatne, bez refs i releases. Zachowano branch,
historię, checkpointy i zastane untracked właściciela. Praca na osobnym
fix/hwvis1-publish2. RELEASE1 `600d934` był bazą funkcjonalną, nie dowodem
poprawności obrazu sprzętowego. A-01–A-03 miały wcześniejszy niezależny odbiór;
tutejsze ponowne testy wykonał ten agent, bez deklaracji niezależnego reviewera.

Zgłoszenie: migotanie końca bootu i następnego poziomu to obserwacja
właściciela; zdjęcia opisują pasy, nie dowodzą przebiegu migotania. Zdjęcia
nie zostały dostarczone jako pliki tej sesji. Uruchomienie z OPTION dowodzi,
że **BASIC OFF jest wymaganiem startu**, a pierwotny czarny ekran nie dowodzi
awarii SIO. Nie przypisano wad telewizorowi.

Atari800 7.1.2 odtworzył błąd na dokładnym normalnym ATR RELEASE1
`fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82`,
z tymi samymi pinami, ekranami i standardowym OS SIO. Rzeczywiste zmienne
emulatora odczytane obserwatorem: XL/XE (enum 1), RAM 64 KB, PAL 312 linii,
BASIC disabled=1, ESC_enable_sio_patch=0. Nie wystarczał sam argument launchera.
Konfiguracje i legalny OS pozostają prywatne; do dowodów trafiają ustawienia
i hashe, nie ROM-y. Headless/turbo dotyczy wyłącznie tempa hosta. Nie zmieniano
emulacji ANTIC, GTIA, POKEY, VBI ani SIO. Dodatkowy observer tylko czyta stan.

**Przyczyna:** FINISH2 dodał dwa DLI loadera, ale `dli_row` zerował własny
**odroczony** VBI. Podczas OS SIO flaga CRITIC ($42) pomija tę część VBI;
DLI nadal wykonuje inkrementację fazy. W porównawczym przebiegu loader
wykonał 2383 DLI, indeks osiągnął 9 zamiast 0–1; pierwsze nieprawidłowe
fazy w klatce 1466 (2,3), przy CRITIC=1. Faza 8/9 czyta poza ośmioma wpisami
tablic. To konkretny błąd programu zależny od rzeczywistego SIO, nie palety TV.
Do tego pierwsze przejęcie loadera po splashu ustawiało tylko kopie OS,
pozostawiając sprzętową paletę poprzedniego ekranu do następnego pełnego VBI.
Przy wejściu do późniejszego loadera DMA czekało na ten sam odroczony VBI.

Podstawa symboli OS: [CRITIC/VVBLKD/SIOV w źródłach cc65](https://github.com/cc65/cc65/blob/master/asminc/atari.inc).
Rozstrzygający dowód jest lokalnym śladem instrukcji, rejestrów i klatek.

**Dekoracja a wada:** `finish2_overlay.py` ustawiało menu PF2=$90/$E0,
loader PF2=$90 i HUD pierwszego wiersza $E0; szerokie niebieskie i brązowe
pasy były celową dekoracją. RELEASE1 zachował te menu/loader DLI. Błędem
jest utrata fazy i niepełna publikacja stanu podczas SIO; dekorację dodatkowo
uproszczono zgodnie z docelowym ciemnym wyglądem.

## Zakres naprawy

`hwvis1_overlay.py` nakłada ograniczoną poprawkę na dotychczasowy builder:

- loader nie ma DLI; ANTIC C ilustracji używa stałego PF0, napis i cienki
  pasek ANTIC F używają PF1/PF2; tło PF2=0 przez cały ekran;
- bootstrap i resident loader ustawiają jednocześnie rejestry sprzętowe
  i kopie OS: DL, font, kolory; gotowy napis, lista i paleta poprzedzają
  publikację asset_loading oraz DMA, przed wejściem w SIO;
- usunięto przedwczesne asset_loading=1 w asset_load_begin; pierwsza faza
  DLI jest jawnie zerowana w inicjalizacji;
- menu zachowuje ilustrację, tytuł, cztery pozycje i strzałkę, z czarnym tłem;
  HUD ma ciemny pierwszy wiersz. DLI planszy i próbkowanie wejścia zachowane.

Nie dodano fast loadera, opóźnień, blokady przerwań podczas OS SIO, zmiany
stosów ani undo. Nie zmieniono mechaniki, kampanii, kafelków, obiektów,
palet Energy/Hydro/Data/Reactor ani playera muzyki. Wszystkie 60 sektorów
plansz i 60 pakietów grafiki są bajtowo równe RELEASE1, również między
wariantami. Walidacja CRC i warunek loaded==1 pozostały. Pauza/config
zatrzymują DMA przed zmianą SCREEN/HUD; show_play odbudowuje ekran i roboczą
listę po przygotowaniu całości. Loader korzysta z własnej ilustracji poza
pakietami planszy/menu; żaden pakiet nie zapisuje aktualnie pokazywanego fontu
loadera. Jego napis jest przygotowywany przed DMA; postęp zmienia mały pasek.

## Dowody przed / po

| Ekran | RELEASE1 | HWVIS1 |
|---|---|---|
| Menu | [natywnie](evidence/menu-before.png) | [natywnie](evidence/menu-after.png) |
| LOADING SHIFT | [natywnie](evidence/loader-before.png) | [natywnie](evidence/loader-after.png) |
| HUD / Energy 01 | [natywnie](evidence/HUD-before.png) | [natywnie](evidence/HUD-after.png) |

[Archiwum kolejnych natywnych klatek, pinów i CSV](evidence/native-transitions.zip)
zawiera boot/handover (470–520, 1400–1950), koniec bootu i menu, Begin Shift
(3200–4100), następny poziom (4700–5400), pause/config/resume (5780–6010),
oraz granice 15→16, 30→31, 45→46 i finał (4650–5350). Są to pełne sekwencje
klatek w podanych oknach, nie tylko poprawne końcowe screenshoty. Osobne
frame traces obejmują także przerwy poza oknami PNG. Wejścia są urządzeniowe,
bez wstrzykiwania stanu RAM. Krótkie drogi graniczne używają jawnie opisanych
save na **prywatnych kopiach** ATR. Nie wchodzą do player ZIP ani Draftu.

Przed naprawą ten sam napis miał **cztery różne rastry w 400 kolejnych klatkach**
przy niezmienionym wejściu; po naprawie ma dokładnie jeden. To reprodukcja
migotania w emulatorze, nie wniosek z pojedynczego zdjęcia.
Po naprawie loader ma zero DLI, a statyczna część obrazu pozostaje identyczna
przez 400 kolejnych klatek przy standardowym SIO. [Weryfikacja](verification.json)
wiąże hashe i dokładne okna; osobne framemd5 obejmują ilustrację/tło
(336×144 od y=24) oraz wiersz napisu (336×8 od y=176), bez paska postępu.
Pełne PNG obejmują również te elementy i przejścia. Zwykłe przygaszenie DMA
podczas budowania nowego ekranu pozostaje; nie jest maskowane opóźnieniem.

## Regresje końcowego ATR

- [60 rozwiązań i finał](campaign60.json): gotowy normalny ATR, pełny cold
  boot, standardowy OS SIO (`-nopatch`), rzeczywiste piny, 120 raster checks
  stanów początkowych/rozwiązanych; 121538 klatek PAL w całym przebiegu.
- [A-01](A01.json): oryginalny świadek audytu, FIRE odczytany wewnątrz akcji,
  17 faz kierunku, pięć zablokowanych prób, osobne rastry ruchu i undo.
  [Finał i zimny Continue ukończenia](hardware-routes.json): dodatkowy świadek
  na poziomie 60 i pięć faz, bez przedwczesnego finału.
- [A-02](A02.json): 1088 przypadków sim65 rzeczywistego campaign.c i crc.s;
  [A-03/zapisy](saves-tests.json): awarie odczytu slotów, write protect,
  prawidłowe generacje, fallback semantyczny, izolacja normal↔test↔test,
  stock write i cold Continue; [normal fallback](normal-fallback.json).
- [Undo256](undo256.json): 270 ruchów z ATR, cofnięcie ostatnich 256 do
  dokładnego prefiksu 14. Restart/pauza/config/powrót i cztery testowe starty
  sprawdzone. ASan/UBSan i sim65 obejmują wszystkie ścieżki rozwiązań/prefiksy.
- Dwa źródłowe snapshoty bez poprzednich buildów dają identyczny normalny ATR.
  Granice linkera, 2048 B stosu C, 256 B stosu sprzętowego, undo256 zachowane;
  wolne MAIN: 68 B normalny / 48 B testowe; LOW 23 B, ZP 52 B, PERSIST 248 B.
  Obserwowane maksima: 21 B stosu C / 36 B sprzętowego, zero próbek poza C;
  szczegóły w verification.json. To pomiar
  zbadanych ścieżek, nie globalny dowód WCET.

Test emulatora nie jest testem sprzętowym ani odsłuchem POKEY/SIO2SD.

## Pakiet, źródła i publikacja

[Pięć obrazów i hashe](candidate.json). Wygeneruj:
`python3 tools/hwvis1_prepare.py`. Pakiet wewnętrzny:
`build/owner-smoke/hwvis1/neon-shift65-hwvis1-owner.zip`, pięć ATR-ów,
SHA256SUMS i [instrukcja PL/EN z OPTION](HARDWARE-SMOKE.md).
Launcher: `PLAY-WINDOWED.command` / `python3 tools/release1_owner_smoke.py`.
Osobne robocze kopie zachowują zapisy; wcześniejsze pakiety pozostają lokalnie.

Normalny ATR, deterministyczny player ZIP, manifest i sumy są w `dist/`.
Odświeżono pięć GIF-ów i sześć PNG, bo wszystkie obejmują zmienione menu,
loader albo HUD. Układ PUBLISH1, ilustracje, treści i właściwe notices
wykorzystano ponownie. [Manifest mediów](../media/manifest.json) wskazuje
pochodzenie, hash ATR, klatki i standardowe SIO. Starszy raport PUBLISH1
pozostaje historyczny; [PUBLISH2 verification](publication-verification.json)
sprawdza paczkę, odnośniki i dokładne RGB kodowanych materiałów.

[Otwarte prawa i konkretne brakujące oświadczenia](RIGHTS.md): Service Current,
20 odziedziczonych map, w szczególności FIRST DOCK/REACTOR STORE; referencja
bitmapowa poza eksportem. Brak autorstwa nie jest wypełniany domysłem.

Czysty eksport jest aktualizacją przygotowanego eksportu PUBLISH1, osobnym
repozytorium z niezależnym pierwszym commitem. Historia źródłowa nie została
przepisana. [Wynik eksportu/push/Draft i świeżego checkoutu](publication.json)
wiąże źródłowy checkpoint z rzeczywistym zdalnym commitem. Nie zawiera .git
oryginału, prywatnych konfiguracji, ROM-ów, zapisów właściciela ani wielkich
historycznych archiwów. Testowe ATR-y zostają wyłącznie lokalnie.

## Pozostaje do odbioru

Właściciel: OPTION/BASIC OFF, końcówka ładowania, menu/wybór, HUD, następny
poziom, wszystkie cztery obszary, pause/config/resume, zapis i zimne Continue,
muzyka/SFX na Atari + SIO2SD. Do tego oświadczenia o prawach wskazane wyżej.
Do tego czasu OWNER_PENDING, prywatny Draft, bez finalnego v1.0.0.
