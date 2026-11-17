"""Render a minimal Routing block via flows_sdk to capture the exact HSDSL shape."""
import json
from flows_sdk.blocks import Routing, Block


class _Passthrough(Block):
    def __init__(self, reference_name, value):
        super().__init__(reference_name=reference_name, identifier="PYTHON_3_12_CODE",
                         input={"data": {"v": value}, "code": "# stub"})


r = Routing(
    reference_name="probe_routing",
    decision="${workflow.input.perf_test_mode}",
    branches=[
        Routing.Branch(case="true",  blocks=[_Passthrough("bypass_branch", "true")],  label="perf-bypass", output="bypass_branch"),
        Routing.Branch(case="false", blocks=[_Passthrough("normal_branch", "false")], label="normal",      output="normal_branch"),
    ],
    default_branch=Routing.DefaultBranch(blocks=[_Passthrough("default_branch", "def")], output="default_branch"),
    title="Probe Routing",
    description="probe",
)

print(json.dumps(r.render(), indent=2))
