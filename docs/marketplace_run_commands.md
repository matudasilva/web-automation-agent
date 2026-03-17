# Marketplace Run Commands

Useful commands for running the Marketplace group-share flow and inspecting per-group outcomes.

## Run And Save Output

Run the flow and keep a copy of the terminal output:

```bash
python -m src.main | tee /tmp/marketplace-run.log
```

`src.main` also writes a JSON log file automatically for each run under `logs/`:

```bash
ls -1t logs/*_src_main.log | head -n 1
```

## Show Per-Group Outcome Logs

Filter the new per-group summary events:

```bash
rg "marketplace_group_share_batch_group_(attempt|final)_result" /tmp/marketplace-run.log
```

Or read them from the latest automatic log file:

```bash
rg "marketplace_group_share_batch_group_(attempt|final)_result" "$(ls -1t logs/*_src_main.log | head -n 1)"
```

## Show Only Final Group Results

Useful for a compact summary of success, retry, approval, or skip results:

```bash
rg "marketplace_group_share_batch_group_final_result" /tmp/marketplace-run.log
```

## Show Groups That Need Approval

```bash
rg "post_publish_status=submitted_for_approval" /tmp/marketplace-run.log
```

## Show Groups That Need Retry

```bash
rg "post_publish_status=publish_needs_retry" /tmp/marketplace-run.log
```

## Show Successful Auto/Manual Publish Confirmations

```bash
rg "post_publish_status=publish_success_confirmed" /tmp/marketplace-run.log
```

## Show Groups Skipped After Exhausting Attempts

```bash
rg "final_result=skipped_after_" /tmp/marketplace-run.log
```

## Show Flow Failures

```bash
rg "marketplace_group_share_flow_failed|marketplace_group_share_batch_group_attempt_failed" /tmp/marketplace-run.log
```

## Show Group Iteration Order

```bash
rg "marketplace_group_share_batch_iteration_start" /tmp/marketplace-run.log
```

## Suggested Review Sequence

1. Run the flow with `tee`.
2. Review final group results.
3. Review approval and retry statuses.
4. Review skipped groups and failures if needed.
