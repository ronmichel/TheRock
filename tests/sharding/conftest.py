import os
import re
import sys
import time
import pytest

import logging

logging.getLogger("urllib3").setLevel(logging.WARNING)

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from libs import utils
from libs.utils import log
from libs import nodes
from libs import orchestrator


def pytest_addoption(parser):
    parser.addoption("--rock", action="store", default="/therock", help="the rock path")
    parser.addoption(
        "--env", nargs="+", action="store", default=[], help="provide extra env"
    )


@pytest.fixture(scope="session")
def extraEnv(pytestconfig):
    return dict(e.split("=") for e in pytestconfig.getoption("env"))


@pytest.fixture(scope="session")
def rock(pytestconfig):
    return pytestconfig.getoption("rock")


@pytest.fixture(scope="session")
def node(rock):
    return nodes.Node()


@pytest.fixture(scope="session")
def orch(node):
    return orchestrator.Orchestrator(node)


@pytest.fixture(scope="session")
def report(request):
    from libs import report

    report = report.Report()
    yield report
    verdict = not (request.session.testsfailed)
    report.pprint()
    fd = open("report.html", "w")
    fd.write(report.toHtml())
    fd.close()


@pytest.fixture(scope="class")
def table(report):
    table = report.addTable(title="Test Report:")
    table.addHeader("Test", "Verdict", "ExecTime")
    return table


@pytest.fixture(scope="function")
def result(pytestconfig, request, report, table):
    report.testVerdict = False
    startTime = time.time()
    yield report
    testName = request.node.name
    verdictStr = ("FAIL", "PASS")[report.testVerdict]
    execTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
    table.addResult(testName, verdictStr, execTime)


@pytest.fixture(scope="function")
def dmesgs(request, node):
    node.runCmd("dmesg", "-c")
    yield
    ret, out = node.runCmd("dmesg", "-c", out=True, verbose=None)
    fd = open(f"dmesg_{request.node.name}.log", "wb")
    fd.write(out)
    fd.close()


@pytest.fixture(scope="session")
def ompEnv():
    return {
        "OMP_NUM_THREADS": "{int((self.getCpuCount()*0.8)/self.getGpuCount()) or 1}"
    }
