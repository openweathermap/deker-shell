import pytest

from ptpython import history_browser


@pytest.fixture
def restored_history_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leaves the history browser module of ptpython as it was: configure() and insert_in_selection_order() change it.

    :param monkeypatch: undoes the changes at the end of the test
    """
    module = vars(history_browser)
    monkeypatch.setitem(module, "HistoryMapping", module["HistoryMapping"])
    if "sorted" in module:
        monkeypatch.setitem(module, "sorted", module["sorted"])
    else:
        monkeypatch.delitem(module, "sorted", raising=False)
