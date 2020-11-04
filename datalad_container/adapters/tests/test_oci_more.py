"""Tests of oci adapter that depend on skopeo or docker being installed.

See datalad_container.adapters.tests.test_oci for tests that do not depend on
this.
"""
from distutils.spawn import find_executable

from datalad.api import (
    Dataset,
    # FIXME: This is needed to register the dataset method, at least when
    # running this single test module. Shouldn't that no longer be the case
    # after datalad's 4b056a251f (BF/RF: Automagically find and import a
    # datasetmethod if not yet bound, 2019-02-10)?
    containers_add,
)
from datalad.cmd import (
    StdOutErrCapture,
    WitlessRunner,
)
from datalad_container.adapters import oci
from datalad_container.adapters.utils import get_docker_image_ids
from datalad.tests.utils import (
    assert_in,
    integration,
    skip_if_no_network,
    SkipTest,
    slow,
    with_tempfile,
)

for dep in ["skopeo", "docker"]:
    if not find_executable(dep):
        raise SkipTest("'{}' not found on path".format(dep))


@skip_if_no_network
@integration
@slow  # ~13s
@with_tempfile
def test_oci_add_and_run(path):
    ds = Dataset(path).create(cfg_proc="text2git")
    ds.containers_add(url="oci:docker://busybox:1.30", name="bb")

    image_path = ds.repo.pathobj / ".datalad" / "environments" / "bb" / "image"
    image_id = oci.get_image_id(image_path)
    existed = image_id in get_docker_image_ids()

    try:
        out = WitlessRunner(cwd=ds.path).run(
            ["datalad", "containers-run", "-n", "bb",
             "sh -c 'busybox | head -1'"],
            protocol=StdOutErrCapture)
    finally:
        if not existed:
            WitlessRunner().run(["docker", "rmi", image_id])
    assert_in("BusyBox v1.30", out["stdout"])