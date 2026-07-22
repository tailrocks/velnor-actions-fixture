# GitHub Actions runner policy

Every executable positive fixture uses one canonical YAML shape on all lanes:

- `velnor` is the automatic and manual default and uses the selected
  `velnor-trusted` group with label `velnor-target-mvp`.
- `github` is the explicit comparison/recovery lane on `ubuntu-26.04`.
- `both` executes identical positive workload jobs on both lanes.

The canonical Sunday parity schedule selects `both`. Only
`matrix.config.writer` may gate mutations and must select exactly one writer.
Negative fixtures preserve the exact unsupported input or missing permission
they prove; never weaken or delete them to satisfy Velnor.

Rust compile jobs use mold and local-only sccache v0.16.0 with a 20 GiB bound.
Use `cargo nextest run`, never `cargo test`. Every remote action is pinned to a
full commit SHA. Every job has measured `timeout-minutes`; every executable
workflow has intentional concurrency. Fix fixture failures in Velnor.

