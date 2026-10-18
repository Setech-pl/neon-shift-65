"""Report measured per-bank proposals and final allocation without pooling."""
import json,csv
from pathlib import Path
B=Path('build/eng3-observed-input-3pal');D=Path('docs/checkpoints/art3-contextual-decoration');E=D/'evidence'
p=json.loads((B/'proposal-measurements.json').read_text());r=json.loads((B/'resource-measurements.json').read_text())
lines=['# ART3 — zasoby i koszty','', 'Finalne pomiary:64 identyczne XEX i mapy względem ART2.1. MAIN80B, skrajny carry32B, LOW75B, ZP66B. Wzrost resident0B, nowych buforów0B. Pięć osobnych banków1024B; każdy ma4 sloty124–127 zarezerwowane dla robota. Wolnych slotów ani dziur pamięci nie sumujemy między bankami.','', 'Pakiet8624B RAW /8768B na dysku. Transfer:5120 banki +1280 robot +880 tło +800 kompozycja +544 descriptor. Aktywny descriptor384B, metadata8B; transferowy nadmiar to istniejący overlay. ATR1048592B,507 przydzielonych sektorów. Aktywna suma rezerwacji46610B, konserwatywny szczyt przejścia46994B, bez wzrostu. To union stałych rezerwacji z pełnymi stosami C2048B/HW256B, nie pomiar dynamicznego high-water. Aktualność union potwierdza niezmienność wszystkich adresów/rezerwacji i długości sekcji.','', '| Obszar | ART2.1 minimum wolnych | ART3 minimum wolnych |','|---|---:|---:|']
for a,old in enumerate([29,25,28,37],1):lines.append(f'|{a}|{old}|{r[a-1]["min_free_glyphs"]}|')
lines+=['','## Porównanie propozycji przed wdrożeniem','','Generator zmierzył A/B osobno dla2fixture ×3sceny ×5banków. Obie propozycje zachowują rozmiary sekcji; A używa istniejących wariantów ścian, B dodaje dwupikselowy detal wnętrza rzadkiej prostej ściany. Tabela pokazuje zakresy **w danym banku** po wszystkich6scenach, nie sumę dostępnej pamięci. N=nowe unikalne wzory względem ART2.1 w tym banku, R=wycofane wzory, S=zmienione sloty po deterministycznym przepakowaniu. N obejmuje replikację istniejącego urządzenia do innego pasa; nie oznacza N nowych rysunków. Pełna lista perfixture/scene/bank jest w proposal-measurements.json i CSV.','','| Wariant | Area | Bank | N | R | S | Min wolnych |','|---|---:|---:|---:|---:|---:|---:|']
rows=[]
for variant in ['A','B']:
 for area in range(1,5):
  jobs=[j for j in p if j['job'][:2]==[variant,area]]
  for bank in range(5):
   values=[s['banks'][bank] for j in jobs for s in j['scenes']]
   ran=lambda key:f'{min(v[key] for v in values)}–{max(v[key] for v in values)}'
   lines.append(f'|{variant}|{area}|{bank}|{ran("new_patterns")}|{ran("retired_patterns")}|{ran("changed_slots")}|{min(v["free"] for v in values)}|')
  for j in jobs:
   for s in j['scenes']:
    for v in s['banks']:rows.append(dict(proposal=variant,area=area,fixture=j['job'][2],scene=s['scene'],**v,RAW=s['RAW'],encoded=s['disk']))
with (E/'proposal-banks.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
lines+=['','## Przygotowanie planszy i runtime','','Obie propozycje wybierają dekorację poza Atari. Istniejące800B kompozycji zawiera prawidłowy kod każdej ćwiartki. Przygotowanie planszy i zwolnionego pola używa tych samych pętli/odczytów/zapisów; nie dochodzi żadna praca dekoracyjna perframe. Animacje zachowują uporządkowaną listę(period,phase,4decoded glyphs), liczbę rekordów i kod harmonogramu. Dla propozycji A poza zbudowanymi egzemplarzami0B resident jest wnioskiem ze stałych danych C/ASM i sekcji, a nie dodatkowym pomiarem linkera. Dla finalnych64wariantów to pomiar binarny.','', 'Zmierzone maxima CPU exclusive finalnego replay/carry (clocks6502, nie średnie; nie zastępują external-t0 bramek):','','|Area|dirty cells|robot/dock prepare|publication|ambient|native DLI|','|---|---:|---:|---:|---:|---:|']
for area in range(1,5):
 d=json.loads((B/f'area-{area}/game-measurements.json').read_text());m={}
 for k in ['replay','hud']:
  for v in d[k]['CPU']['procedures']:m[v['name']]=max(m.get(v['name'],0),v['max_cpu'])
 lines.append(f'|{area}|{m["dirty_cells"]}|{m["robot_dock_prepare"]}|{m["publication"]}|{m["ambient"]}|{m["native_DLI"]}|')
lines+=['','Nie utożsamiamy niezmienionego kodu z identyczną latencją: CRC/dane ładowanego pakietu mogą zmienić wyrównanie pracy do klatki. Wyniki graniczne i klasyfikacja regresji są osobno w review/report. Nie ma kosztu nowego mechanizmu do przeniesienia do ENG1. Przezroczysta kompozycja pod obiektem pozostaje poza zakresem; obecne obiekty są niezmienionymi pełnymi tile.','']
(D/'resource-headroom.md').write_text('\n'.join(lines))
print('PASS resource report and',len(rows),'per-bank proposal rows')
