import sys
import time

from testcases import CheckOpenAPIAvailability, CreateSinglePost, CreateSinglePostWithTags, CreatePostWithInvalidTags, \
    CreateHugeAmountOfPosts

TESTS = [
    CheckOpenAPIAvailability(),
    CreateSinglePost(),
    CreateSinglePostWithTags(),
    CreatePostWithInvalidTags(),
    CreateHugeAmountOfPosts()
]


def main():
    print("Running Tutter e2e tests...")
    print("-------------")
    passed = 0
    failed = 0
    total = 0
    total_start_time = time.time()
    for test in TESTS:
        total += 1
        print(test.__class__.__name__, "...", end="", flush=True)
        test_case_started = time.time()
        success = True
        try:
            test()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            success = False
            print()
            print("Exception:", e)
            print()

        test_case_time = time.time() - test_case_started

        if success:
            print("PASS", end="")
            passed += 1
        else:
            print("FAIL", end="")
            failed += 1

        print(f" ({test_case_time:.3f}s)")

    total_test_time = time.time() - total_start_time
    assert total == len(TESTS)
    assert passed + failed == total

    print("-------------")
    print(f"Total time: {total_test_time:.3f} seconds")
    print("Tests run:", total)
    print("Failed tests:", failed)
    print("Passed tests:", passed)
    print("-------------")
    if failed > 0:
        print("FAIL")
    else:
        print("GREAT SUCCESS")
    print("-------------")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
