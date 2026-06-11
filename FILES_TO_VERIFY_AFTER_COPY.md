# Files to verify after copying BeBe Ops v2.3

Check these in GitHub before running again:

1. `.github/workflows/hsd-pipeline-control-v1.yml`

Expected first lines:

```yaml
name: Her Sports Daily Production Controller v3.2.4 BeBe Ops v2.3
run-name: HSD BeBe Ops v2.3 • ${{ github.event.inputs.run_mode || 'full_pipeline' }} • run ${{ github.run_number }}
```

Expected artifact name:

```yaml
name: hsd-production-control-v3-2-4-bebe-ops-v2-3-lite-review-${{ github.run_number }}
```

2. `config/pipeline_version.json`

Expected:

```json
"pipeline_version": "v3.2.4-bebe-ops-v2.3"
```

3. `verify_hsd_install_v1.py`

Expected:

```python
VERSION = "hsd-install-verifier-v3.2.4-bebe-ops-v2.3"
EXPECTED_PIPELINE_VERSION = "v3.2.4-bebe-ops-v2.3"
```

4. `generate_hsd_pipeline_review_lite_v1.py`

Expected:

```python
VERSION = "hsd-pipeline-review-lite-v3.2.4-bebe-ops-v2.3"
```

## Important

If GitHub still shows this older name, the hidden workflow did not get copied:

```text
Her Sports Daily Production Controller v3.2.1 BeBe Ops v2
```
