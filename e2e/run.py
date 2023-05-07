import sys
import time
import traceback

from lib import TestCaseBase
from inspect import isclass
import pkgutil
from importlib import import_module


def load_tests() -> list:
    modules = []

    for _, name, is_pkg in pkgutil.walk_packages(["tests"]):
        if is_pkg:
            continue

        if not name.startswith('test_'):
            continue

        fullpath = 'tests.' + name

        module = import_module(fullpath)

        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            if isclass(attribute):

                if not issubclass(attribute, TestCaseBase) or attribute is TestCaseBase:
                    continue

                # Add the class to this package's variables
                globals()[attribute_name] = attribute

                instance = attribute()  # create new instance

                modules.append(
                    instance
                )

    modules.sort(key=lambda t: t.priority, reverse=True)  # put higher priority first

    return modules


def main():
    print("Running Tutter e2e tests...")
    print("=============")
    passed = 0
    failed = 0
    total = 0
    tests = load_tests()
    if len(sys.argv) > 1:
        selected_tests = list(filter(lambda t: t.__class__.__name__ in sys.argv[1:], tests))
    else:
        selected_tests = tests

    assert len(selected_tests) <= len(tests)

    total_start_time = time.time()
    for test in selected_tests:
        test_name = test.__class__.__name__
        total += 1
        print(f"[{total}/{len(selected_tests)}]", test_name, "...", end="", flush=True)
        test_case_started = time.time()
        success = True
        post_info = None
        try:
            test()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            success = False
            tb = traceback.format_exc()
            post_info = f"""
Exception: {e}

{tb}
"""

        test_case_time = time.time() - test_case_started

        if success:
            print("PASS", end="")
            passed += 1
        else:
            print("FAIL", end="")
            failed += 1

        print(f" ({test_case_time:.3f}s)")

        if post_info:
            print(post_info)
            print("---------------------------------")

    total_test_time = time.time() - total_start_time
    assert total == len(selected_tests)
    assert passed + failed == total

    print("=============")
    print(f"Total time: {total_test_time:.3f} seconds")
    print("Tests run:", total)
    print("Failed tests:", failed)
    print("Passed tests:", passed)
    print("=============")
    if failed > 0:
        print("FAIL")
    else:
        print("GREAT SUCCESS")
    print("=============")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
