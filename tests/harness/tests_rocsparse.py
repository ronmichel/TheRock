#!/usr/bin/python3


class TestRocSparse:
    """This is an Pytest Test Suite Class to test RocSparse component of TheRock"""

    def test_rocsparse(
        self, orch, ompEnv, rocsparseMatricesDir, rocsparseTestDir, result
    ):
        """A Test case to verify RocSparse tests"""
        result.verdict = orch.runGtest(
            "./rocsparse-test",
            gfilter="quick/spmm_bell.level3/*",
            env={
                "ROCSPARSE_CLIENTS_MATRICES_DIR": rocsparseMatricesDir,
                **ompEnv,
            },
            cwd=rocsparseTestDir,
            cwd=f"{therock_path}/bin"
        )
        assert result.verdict
