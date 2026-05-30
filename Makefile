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

all:
	make check
	make fix
	make test
	make status
	make diff