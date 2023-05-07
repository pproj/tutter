from abc import ABC, abstractmethod


# Errors

class JsonTreeError(Exception):
    pass


class JsonTreeValueMismatchError(JsonTreeError):
    def __init__(self, key_hint: str, got, expected):
        pass


class JsonTreeMissingKeyError(JsonTreeError):
    def __init__(self, key_hint: str, key):
        pass


class JsonTreeNotMissingKeyError(JsonTreeError):
    def __init__(self, key_hint: str, key):
        pass


class JsonTreeMagicError(JsonTreeError):
    def __init__(self, key_hint: str, error: str):
        pass


# Magic stuff

class JsonTreeMagic(ABC):

    @abstractmethod
    def compare(self, key_hint: str, exists: bool, got):
        pass


class MagicExists(JsonTreeMagic):

    def compare(self, key_hint: str, exists: bool, got):
        if not exists:
            JsonTreeMissingKeyError(key_hint, None)


class MagicNotExists(JsonTreeMagic):

    def compare(self, key_hint: str, exists: bool, got):
        if exists:
            JsonTreeNotMissingKeyError(key_hint, None)


class MagicAnyNumeric(JsonTreeMagic):

    def compare(self, key_hint: str, exists: bool, got):
        if not exists:
            JsonTreeMissingKeyError(key_hint, None)

        try:
            int(got)
        except ValueError:
            raise JsonTreeMagicError(key_hint, f"Value {got} could not be casted to int")


class MagicAnyString(JsonTreeMagic):

    def compare(self, key_hint: str, exists: bool, got):
        if not exists:
            JsonTreeMissingKeyError(key_hint, None)

        if not isinstance(got, str):
            raise JsonTreeMagicError(key_hint, f"Value {got} is not string")


class MagicUnorderedList(JsonTreeMagic):

    def __init__(self, expected: list):
        self.expected = expected

    def compare(self, key_hint: str, exists: bool, got):
        if not exists:
            JsonTreeMissingKeyError(key_hint, None)

        if (not isinstance(got, list)) or (len(self.expected) != len(got)):
            raise JsonTreeValueMismatchError(key_hint, got=got, expected=self.expected)

        for expected_item in self.expected:
            if expected_item not in got:
                raise JsonTreeMagicError(key_hint, f"Item {expected_item} is missing from list: {got}")


class MagicAnyOf(JsonTreeMagic):

    def __init__(self, expected: list):
        self.expected = expected

    def compare(self, key_hint: str, exists: bool, got):
        if not exists:
            JsonTreeMissingKeyError(key_hint, None)

        if got not in self.expected:
            raise JsonTreeMagicError(key_hint, f"Item {got} not any of {self.expected}")


# main compare stuff
def expect_json_tree(got, expected, key_hint=None):
    if not key_hint:
        key_hint = ""

    if isinstance(expected, dict):

        if not isinstance(got, dict):
            raise JsonTreeValueMismatchError(key_hint, got, expected)

        for key, value in expected.items():
            if key not in got.keys():
                if isinstance(expected, JsonTreeMagic):
                    expected.compare(f"{key_hint}.{key}", False, None)
                else:
                    raise JsonTreeMissingKeyError(key_hint, key)
            else:
                expect_json_tree(got[key], value, key_hint=f"{key_hint}.{key}")

    elif isinstance(expected, JsonTreeMagic):
        expected.compare(key_hint, True, got)

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
