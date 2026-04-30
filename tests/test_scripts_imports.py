import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "app.scripts.inspect_relationship_candidates",
        "app.scripts.backfill_relationship_reviews",
        "app.scripts.inspect_document",
        "app.scripts.process_document",
    ],
)
def test_script_modules_import(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None
