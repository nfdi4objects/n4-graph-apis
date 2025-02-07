test: .venv
	.venv/bin/python -m pytest

.venv: requirements.txt
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

dev: .venv
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/python app.py --debug

lint: .venv
	@.venv/bin/flake8 *.py app/*.py tests/*.py --select=E9,F63,F7,F82 --show-source --statistics
	@.venv/bin/flake8 *.py app/*.py tests/*.py --ignore=C901 --exit-zero --max-complexity=10 --max-line-length=127 --statistics

fix: .venv
	@.venv/bin/autopep8 --in-place *.py app/*.py tests/*.py

docker:
	@docker build -t n4o-graph-apis .
