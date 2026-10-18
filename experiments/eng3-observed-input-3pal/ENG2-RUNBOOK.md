# ENG2 — właściwy zakres poleceń

Canonical dokumentacja: `docs/checkpoints/eng2-capture-publication-feasibility/README.md`.
Plik `README.md` tego source fork jest odziedziczony z ENG1/ART3 i zachowany w
niezmiennym169-file freeze; nie stanowi instrukcji uruchamiania ENG2.

Wykonane polecenia ENG2 to setup, run_matrix build/game, observer_build,
capture_cases, capture_short_pairs, exact_counterfactual_pairs, measure_capture,
qualification engine/phase/floor/UX/audio/focused/measure, boundary_queries,
publication_solver, resources, rebuild, freeze_checkpoint, rebuild_archive,
finish_measurements i latch_model_fix. Setup/freeze/build helpers wymagają
pustych odpowiednich outputów; nie należy nadpisywać obecnego freeze/raw.

`candidate-binding.json` i `source-freeze.tar.gz` pozostają niezmienne.
Post-freeze report tools oraz corrected host observer mają odrębne manifesty.
Nie uruchamiać odziedziczonych legacy freeze/seal/report helperów, które mogą
odwoływać się do wcześniejszych checkpointów. Właścicielskiego GUI launcher
agent używa wyłącznie z `--check`; wszystkie emulatory agenta są headless.
