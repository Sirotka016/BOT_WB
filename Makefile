.PHONY: run dev-install run-m

run:
	python main.py

dev-install:
	pip install -e .

run-m:
	python -m bot_wb.main
