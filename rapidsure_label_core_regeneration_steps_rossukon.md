# Update the RapidSure Label and Regenerate the Core Intent Catalog

## Purpose

Change the displayed intent label from `RapidSure Request` to `RapidSure F&W Request` through the Python source and build process. Keep the persisted Salesforce value `RapidSure_Request` unchanged.

These are instructions for proposed code changes. Creating this guide does not apply the changes or regenerate the flow.

## Scope and Prerequisites

- Change only [build_flow.py](../build_flow.py) manually. Do not edit any flow JSON manually.
- Use the existing Endorsement core artifact in `refactored_export/flows` as the build baseline. Confirm it is the intended current version before running the build.
- Keep an unchanged backup of the existing core artifact so the generated result can be compared with it.
- Leave the wrapper, models, Layout Release, connector, and payload code unchanged.
- Do not run `_patch_intents_from_prev.py` for this label-only change: its current implementation applies performance-test overlays and synchronizes other code even with `--core-only`.
- Use the project's configured `.venv` with its existing Flow SDK dependencies installed.

## 1. Change the RapidSure Display Label

In [build_flow.py](../build_flow.py), locate this entry in `INTENT_LABELS`:

```python
"RapidSure_Request": "RapidSure Request",
```

Replace it with:

```python
"RapidSure_Request": "RapidSure F&W Request",
```

Do not change the key `RapidSure_Request`. Only the displayed label changes.

## 2. Add the Core Intent Build Option

Add `import sys` alongside the existing imports in [build_flow.py](../build_flow.py):

```python
import json
import sys
```

Add the following function immediately above the existing `main()` function:

```python
def regenerate_core_intents() -> None:
    flows_dir = Path(__file__).resolve().parent / "refactored_export" / "flows"
    candidates = []
    for path in flows_dir.glob("*.json"):
        flow = json.loads(path.read_text(encoding="utf-8"))
        if flow.get("title") == "Endorsement Custom Core Flow_V41":
            candidates.append((path, flow))
    if len(candidates) != 1:
        raise RuntimeError("Expected exactly one Endorsement core artifact.")

    core_path, core = candidates[0]
    builders = [
        block for block in core.get("blocks", [])
        if block.get("reference_name") == "build_supervision_template"
    ]
    if len(builders) != 1:
        raise RuntimeError("Expected exactly one supervision template builder.")

    builders[0]["input"]["data"]["intent_oneof"] = INTENT_SCHEMA_ONEOF
    core_path.write_text(json.dumps(core, indent=2), encoding="utf-8")
    print(f"Regenerated core intent catalog: {core_path}")
```

At the start of the existing `main()`, before `core_path = _write(...)`, add:

```python
    if sys.argv[1:] == ["--core-intents-only"]:
        regenerate_core_intents()
        return
    if sys.argv[1:]:
        raise SystemExit("Supported option: --core-intents-only")
```

Keep the remainder of `main()` unchanged. The new option returns before the normal core/wrapper generation logic runs.

### What This Build Mode Does

- Generates `intent_oneof` from the canonical Python mapping, `INTENT_SCHEMA_ONEOF`.
- Writes that generated catalog into the existing Endorsement core artifact automatically.
- Preserves the core UUID, manifest identifier, block code, and other configuration.
- Does not regenerate the wrapper, synchronize payload code, or apply performance-test changes.

This is a targeted core intent-catalog rebuild, not a reconstruction of every core block. It replaces the entire intent catalog with the Python-defined catalog, so check for unintended catalog differences before importing.

## 3. Run the PowerShell Commands

Open the VS Code PowerShell terminal and move to the project root:

```powershell
Set-Location 'C:\Users\rohchallapalli\OneDrive - Deloitte (O365D)\Documents\HS Drop Down Custom Flow'
```

Check Python syntax:
My python.exe path : C:\Users\rklaber\HS\Workplace\.venv_endt\Scripts\python.exe
My file.py path : C:\Users\rklaber\HS\Workplace\build_flow.py
I'm at : (.venv_endt) PS C:\Users\rklaber\HS\Workplace>
```powershell
& '.venv_endt\Scripts\python.exe' -m py_compile 'build_flow.py'
```

Stop if this command reports an error. Otherwise, regenerate only the core intent catalog:

```powershell
& '.venv_endt\Scripts\python.exe' 'build_flow.py' --core-intents-only
```

Expected output:

```text
Regenerated core intent catalog: ...\refactored_export\flows\<existing-core-filename>.json
```

Do not run `build_flow.py` without the new option for this update. The existing default mode generates both generic core and wrapper artifacts in the project root.

## 4. Validate the Generated Core

Compare the generated core with the unchanged backup using a JSON-aware comparison. Confirm:

- The only intended semantic difference is the label changing from `RapidSure Request` to `RapidSure F&W Request`.
- The RapidSure persisted value remains `RapidSure_Request`.
- The intent count and ordering remain unchanged.
- The core UUID, manifest identifier, block wiring, and other settings remain unchanged.
- No wrapper files, payload code, or performance-test configuration changed.

If other intent entries or configuration values differ, stop and investigate before packaging or importing. Do not manually repair the generated JSON; correct the Python source/build process and regenerate it.

## 5. Import and Verify

1. Follow the approved change process and core-only import/package procedure for your Hyperscience version.
2. Import the generated Endorsement core artifact as an update to the existing core, not as a new flow.
3. Leave the wrapper, models, Layout Release, and output connector unchanged.
4. Open a new Custom Supervision task and verify both intent dropdowns show `RapidSure F&W Request`.
5. Select the renamed option and confirm the Salesforce-bound output still contains `RapidSure_Request`.
6. Confirm existing intent and transaction-type selections continue to work as expected.

If validation fails, restore the previous approved core version through the authorized rollback procedure.