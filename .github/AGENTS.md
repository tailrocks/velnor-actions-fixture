# GitHub Actions runner policy

Every executable positive fixture uses one canonical YAML shape on all lanes:

- `both` is the automatic and manual default for positive paths and executes
  identical local reusable suites on both lanes.
- Classify every scenario as mandatory dual-lane, an explicitly evidenced
  hosted-only/secret-gated exception, or an explicitly evidenced microVM
  expected-unsupported case; never silently downgrade a mandatory scenario.
- `github` and `velnor` are explicit diagnostic single-lane selectors only.
- Public untrusted PRs are hosted-only; Pages has one hosted writer; mutation
  and secret-gated jobs remain explicitly gated. Negative admission and queue/
  backend diagnostics may remain Velnor-only.

The canonical Sunday parity schedule selects `both`. Only
`matrix.config.writer` may gate mutations and must select exactly one writer.
Negative fixtures preserve the exact unsupported input or missing permission
they prove; never weaken or delete them to satisfy Velnor.

The default Velnor Rust path is the baseline that Rust coverage must prove: ordinary
`cargo` commands with no `RUSTC_WRAPPER`, no sccache or mbx action, and no `actions/cache`
of `target/`. Explicit sccache is one compatibility scenario among several, never a
requirement placed on every Rust job — mandating it disables Velnor's default acceleration
and leaves the out-of-box path untested. Rust compile jobs use mold; a scenario that
explicitly requests sccache pins it local-only with a 20 GiB bound.
Use `cargo nextest run`, never `cargo test`. Every remote action is pinned to a
full commit SHA. Every job has measured `timeout-minutes`; every executable
workflow has intentional concurrency. Fix fixture failures in Velnor.
Keep cache state workspace-owned; never repair ownership with `sudo`.
