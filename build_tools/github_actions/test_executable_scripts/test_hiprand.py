from ctest_runner import run_ctest_executables

run_ctest_executables(
    timeout_seconds="60",
    repeat=True,
    test_name="hipRAND",
)