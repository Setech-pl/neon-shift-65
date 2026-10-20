# Normal PAL 64 KB release; generated files stay under build/.
OUT ?= build/release
.PHONY: all
all:
	python3 tools/build.py --out $(OUT)
