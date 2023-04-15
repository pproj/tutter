import sys
import time
import traceback

from testcases import CheckOpenAPIAvailability, CreateSinglePost, CreateSinglePostWithTags, CreatePostWithEdgeCaseTags, \
    CreateHugeAmountOfPosts, CreateInvalidPosts, InvalidFilters, PostFiltersByAssociation, OtherPostFilters, \
    FiltersTopLevelBasic, FiltersRelatedBasic, FillFilter, LongPollRace, LongPollBasic

TESTS = [
    CheckOpenAPIAvailability(),
    CreateSinglePost(),
    CreateSinglePostWithTags(),
    CreatePostWithEdgeCaseTags(),
    CreateInvalidPosts(),
    InvalidFilters(),
    PostFiltersByAssociation(),
    OtherPostFilters(),
    FiltersTopLevelBasic(),
    FiltersRelatedBasic(),
    FillFilter(),
    CreateHugeAmountOfPosts(),
    LongPollRace(),
    LongPollBasic()
]


def main():
    print("Running Tutter e2e tests...")
    print("=============")
    passed = 0
    failed = 0
    total = 0
    if len(sys.argv) > 1:
        selected_tests = list(filter(lambda t: t.__class__.__name__ in sys.argv[1:], TESTS))
    else:
        selected_tests = TESTS

    assert len(selected_tests) <= len(TESTS)

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
