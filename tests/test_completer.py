from deker import ArraySchema, DimensionSchema
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from deker_shell.completer import DekerCompleter
from deker_shell.namespace import use


def sample_function(argument: int) -> int:
    return argument


class Sample:
    public_attribute = 1
    _private_attribute = 2

    def method(self) -> None:
        pass


NAMESPACE = {
    "sample_function": sample_function,
    "sample_type": Sample,
    "ArraySchema": ArraySchema,
    "DimensionSchema": DimensionSchema,
    "dims": [],
    "collections": ["test", "temperature", "wind"],
    "use": use,
    "client": object(),
    "_hidden": 1,
    "__dunder__": 2,
}


def complete(text: str, cursor: int | None = None, namespace: dict | None = None) -> dict[str, tuple[str, str]]:
    """Completions for ``text`` with the cursor at ``cursor`` (default: the end): text -> (display, kind)."""
    namespace = NAMESPACE if namespace is None else namespace
    completer = DekerCompleter(lambda: namespace, lambda: namespace, lambda: False)
    document = Document(text, len(text) if cursor is None else cursor)
    event = CompleteEvent(completion_requested=True)
    return {c.text: (c.display_text, c.display_meta_text) for c in completer.get_completions(document, event)}


def test_functions_are_displayed_with_parentheses():
    assert complete("sample_fun") == {"sample_function": ("sample_function()", "function")}


def test_class_attributes_are_suggested_and_mro_and_private_ones_are_hidden():
    completions = complete("sample_type.")
    assert completions["public_attribute"] == ("public_attribute", "instance")
    assert completions["method"] == ("method()", "function")
    assert "mro" not in completions
    assert not any(name.startswith("_") for name in completions)


def test_private_names_appear_once_an_underscore_is_typed():
    assert set(complete("sample_type._")) >= {"_private_attribute"}
    assert set(complete("_")) >= {"_hidden", "__dunder__"}
    assert "_hidden" not in complete("")


def test_shell_presets_come_first():
    """``c`` matches a lot; ``client`` and ``collections`` are listed before everything else."""
    completer = DekerCompleter(lambda: NAMESPACE, lambda: NAMESPACE, lambda: False)
    document = Document("c", 1)
    names = [c.text for c in completer.get_completions(document, CompleteEvent(completion_requested=True))]
    assert names[:2] == ["client", "collections"]
    assert len(names) > 2


def test_argument_position_offers_parameters():
    completions = complete("ArraySchema(dtype=int, di")
    assert completions == {"dimensions=": ("dimensions=...", "param")}


def test_value_position_offers_names():
    """Inside a Deker call the value of an argument still completes from the namespace."""
    completions = complete("ArraySchema(dimensions=di")
    assert "dims" in completions
    assert "DimensionSchema" in completions


class TestUseCompletion:
    def test_all_collections_are_offered_quoted(self):
        assert complete("use(") == {
            '"test"': ("test", "collection"),
            '"temperature"': ("temperature", "collection"),
            '"wind"': ("wind", "collection"),
        }

    def test_typed_prefix_narrows_the_names(self):
        assert set(complete("use(te")) == {'"test"', '"temperature"'}
        assert set(complete("use(w")) == {'"wind"'}
        assert complete("use(x") == {}

    def test_open_quote_is_closed_with_the_same_quote(self):
        assert set(complete('use("te')) == {'test"', 'temperature"'}
        assert set(complete("use('te")) == {"test'", "temperature'"}

    def test_existing_closing_quote_is_not_duplicated(self):
        text = 'use("te")'
        assert set(complete(text, cursor=len('use("te'))) == {"test", "temperature"}

    def test_names_replace_the_typed_prefix(self):
        completer = DekerCompleter(lambda: NAMESPACE, lambda: NAMESPACE, lambda: False)
        text = 'use("tem'
        (completion,) = completer.get_completions(Document(text, len(text)), CompleteEvent())
        assert completion.start_position == -3

    def test_nothing_else_is_offered_inside_use(self):
        assert "sample_function" not in complete("use(sample_fun")

    def test_without_collections_variable_the_stock_completion_is_kept(self):
        namespace = {k: v for k, v in NAMESPACE.items() if k != "collections"}
        assert "sample_function" in complete("use(sample_fun", namespace=namespace)

    def test_use_elsewhere_in_the_line_does_not_matter(self):
        assert "sample_function" in complete('use("test"); sample_fun')
