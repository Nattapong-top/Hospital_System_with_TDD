check:
	ruff check .
	black --check .

fix:
	ruff check . --fix
	black .

status:
	git status

diff:
	git diff

test:
	pytest

coverage:
	pytest --cov=.

typecheck:
	mypy .

run:
	uvicorn api.main:app --reload

pull:
	git checkout main
	git pull origin main

all:
	make check
	make fix
	make test
	make diff
	make status