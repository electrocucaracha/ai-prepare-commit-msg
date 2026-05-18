---
applyTo: "**/*.py"
---

# Python Test Requirement

When a change includes any Python file,
run `make test` before considering the task complete.

If tests fail,
fix the issue and re-run `make test` until it passes,
or clearly report the failure details and blocker.

## Pythonic Coding Standards

### Style and Formatting

- Format all Python code with `black` and sort imports with `isort` (profile `"black"`).
- Use `ruff` for linting;
  address every reported issue before finalising a change.
- Run `make fmt` to apply formatting automatically.

### Type Annotations

- Annotate every public function and method with parameter and return types.
- Use `typing.Union` or the `X | Y` union syntax (Python ≥ 3.10) where needed.
- Use `pathlib.Path` instead of raw strings for filesystem paths.

### Docstrings

- Write docstrings for every public module, class, and function.
- Use the NumPy/Google docstring style already present in this codebase
  (Args / Returns / Raises sections, Examples block).
- Include `doctest`-compatible examples in docstrings where practical,
  because `pytest` is configured with `--doctest-modules`.

### Testing with pytest

- Place tests under `tests/` and name files `test_<module>.py`.
- Use `monkeypatch` to replace external dependencies rather than importing mocks.
- Use `tmp_path` for temporary file-system work.
- Prefer `pytest.raises` context managers to assert expected exceptions.
- Keep test helper / dummy classes minimal and focused.
- Do not use bare `assert` statements outside of test functions.

### General Conventions

- Prefer `pathlib.Path` over `os.path`.
- Use `logging` instead of `print` for diagnostic output in library code.
- Raise specific, descriptive exceptions (e.g., `RuntimeError` with context)
  rather than bare `Exception`.
- Avoid mutable default arguments;
  use `None` and assign inside the function body.

## Idiomatic Python (Hettinger, PyCon US 2013)

The following guidelines are drawn from
_Transforming Code Into Beautiful, Idiomatic Python_ by Raymond Hettinger.

### Looping

- Use `enumerate(iterable)` instead of maintaining a manual index counter.
- Use `zip(a, b)` to iterate over two collections in parallel.
- Use `reversed(seq)` to loop backwards and `sorted(iterable)` to loop in order.
- Use `for/else` to detect when a loop completed without hitting a `break`.

### Unpacking

- Unpack sequences into named variables instead of accessing by index:
  `first, *rest = items`.
- Use `_` as a throwaway variable name for values that are intentionally ignored.

### Dictionaries

- Use `dict.get(key, default)` instead of checking key existence with `in` first.
- Use `collections.defaultdict` for grouping or accumulating into a dict.
- Use `collections.Counter` for counting hashable objects.
- Use `dict.setdefault` only when `defaultdict` is not a better fit.

### Comprehensions and Generators

- Prefer list/dict/set comprehensions over accumulate-and-append loops.
- Use generator expressions (`(x for x in ...)`) when the result is consumed once
  or the dataset is large, to avoid building an intermediate list.

### Strings

- Use `''.join(parts)` instead of repeated `+=` string concatenation.

### Boolean Logic

- Use `any(pred(x) for x in iterable)` and `all(...)` instead of loops with
  boolean-flag variables.
- Write chained comparisons (`a < b < c`) instead of `a < b and b < c`.
- Test truthiness directly (`if items:`) instead of `if len(items) != 0:`.

### Named Tuples

- Use `collections.namedtuple` (or `typing.NamedTuple`) to give structure and
  readable field names to tuple-like data instead of accessing by raw index.

### Context Managers

- Use `with` statements for every resource that has a defined cleanup step
  (files, locks, connections).
- Use `contextlib.contextmanager` to factor out temporary-context setup/teardown
  into reusable helpers.
