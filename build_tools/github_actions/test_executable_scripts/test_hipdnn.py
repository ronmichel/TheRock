from ctest_runner import run_ctest_executables

run_ctest_executables(
    timeout=10,
    repeat=False,
    test_name="hipdnn",
)
