# Current MENUFIX1 + SELECTART1 R6; output must not already exist.
OUT ?= build/release
.PHONY: all atr
all: atr
atr:
	python3 tools/build.py --out $(OUT)
