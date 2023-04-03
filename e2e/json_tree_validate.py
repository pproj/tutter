from abc import ABC, abstractmethod


class JsonTreeError(Exception):
    pass


class JsonTreeValueMismatchError(JsonTreeError):
    def __init__(self, key_hint: str, got, expected):
        pass


class JsonTreeMissingKeyError(JsonTreeError):
    def __init__(self, key_hint: str, key):
        pass


class JsonTreeMagicError(JsonTreeError):
    def __init__(self, key_hint: str, error: str):
        pass


class JsonTreeMagic(ABC):

    @abstractmethod
    def compare(self, key_hint, got):
        pass


class MagicExists(JsonTreeMagic):

    def compare(self, key_hint, got):
        pass


class MagicAnyNumeric(JsonTreeMagic):

    def compare(self, key_hint, got):
        try:
            int(got)
        except ValueError:
            raise JsonTreeMagicError(key_hint, f"Value {got} could not be casted to int")


class MagicUnorderedList(JsonTreeMagic):

    def __init__(self, expected: list):
        self.expected = expected

    def compare(self, key_hint, got):
        if (not isinstance(got, list)) or (len(self.expected) != len(got)):
            raise JsonTreeValueMismatchError(key_hint, got=got, expected=self.expected)

        for expected_item in self.expected:
            if expected_item not in got:
                raise JsonTreeMagicError(key_hint, f"Item {expected_item} is missing from list: {got}")


class MagicAnyOf(JsonTreeMagic):

    def __init__(self, expected: list):
        self.expected = expected

    def compare(self, key_hint, got):
        if got not in self.expected:
            raise JsonTreeMagicError(key_hint, f"Item {got} not any of {self.expected}")


def expect_json_tree(got, expected, key_hint=None):
    if not key_hint:
        key_hint = ""

    if isinstance(expected, dict):

        if not isinstance(got, dict):
            raise JsonTreeValueMismatchError(key_hint, got, expected)

        for key, value in expected.items():
            if key not in got.keys():
                raise JsonTreeMissingKeyError(key_hint, key)

            expect_json_tree(got[key], value, key_hint=f"{key_hint}.{key}")

    elif isinstance(expected, JsonTreeMagic):
        expected.compare(key_hint, got)

    elif isinstance(expected, list):

        if not isinstance(got, list):
            raise JsonTreeValueMismatchError(key_hint, got, expected)

        if len(got) != len(expected):
            raise JsonTreeValueMismatchError(key_hint, got, expected)

        for i, item in enumerate(expected):
            expect_json_tree(got[i], item, key_hint=f"{key_hint}[{i}]")

    else:
        if expected != got:
            raise JsonTreeValueMismatchError(key_hint, got, expected)
