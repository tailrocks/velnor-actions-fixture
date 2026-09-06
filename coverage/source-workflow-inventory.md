# Source Workflow Inventory

Current source inventory captured from Velnor **8090fefd146795f1455e36a55c932b90eb58f730**. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`8090fefd146795f1455e36a55c932b90eb58f730`](https://github.com/tailrocks/velnor/tree/8090fefd146795f1455e36a55c932b90eb58f730).
- Capability manifest: v12, runner crate `0.1.256`.
- Capability identity: `398e24ad107f9fdaf04f2a7b1e15dd320875bedfd2a5e571e7fac283960b5909`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `09d061f34f2451b756379f5f35828ccaf8fe9257e8dbbccd76863eacc7c76921` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `oven-sh/setup-bun`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-docker-docker.yml` | `2647c58b333e2e1e6173fde30d56321b4bda314f20ea258d975773b2a0656e6c` | `_docker-suite.yml` | `actions/checkout`, `docker/setup-buildx-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-docs-docs.yml` | `a4871e728e6082a0922684c7536a7f4e89f76fc85df2544bd8e6be879ef4fba1` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-main.yml` | `53c0a4b4d89875541bf13a41a6d5819fa51f546f4a75ca4558c964f053fa1597` | `ci.yml` | `actions/checkout`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `ed4dee8c5eba1ad1f7acf49baaf6a6ee3855ef21bbcc3333234820087b7bf493` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `opentofu/setup-opentofu`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-policy.yml` | `92132219705fcace00253a42bdb4a9d2b609971fa21ecaf4e09b3e8363a06d27` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `cbf077b35a185eca539bdadf15aa7b2b129a0d4f9da15fc2d98a78680196047d` | `ci.yml` | `actions/checkout`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `f33d962f452406f20144f3d9b8f1c3fc209b5a09863ff4c064a65c2c243055a1` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `4567907059fec373364427d3641e71f285121b28056ff9f4e7e25225a89ad28d` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-unit-collector.yml` | `a76abe4a89f1ddda913f9647ea69b0d2405eb9be7e8ac2d0a4073493834e98b8` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `99ee835adf18815fc7fbb83a1e5c23e8dce6745f5767b0807006500784113f54` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-client.yml` | `1631df3db9a07b959a065149f1dff2749871dd61d48203710486fe2bfb5f16f2` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-control.yml` | `dcab87feff34d1a353c3b77944df385f9feb9c771d3ea90fef51f0e2bfaa029a` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-model.yml` | `5cbbe999c65833eaca7762d30e720cf1edd1e3834848aa62ab184e13b1492775` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-render.yml` | `41e2d08a85cde135665b5e3d79b8c998a29ebcc4dbf8af647bb3cdb9ce63840f` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `7f64de2dabe20e0f178eaac3bbb30d660971581d2d469675c1c2c013eba0b02e` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `428e95d29daa430c8da9d07ea892518acabc8cefd110903b9d4b7602afea1367` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `6e957ffb7f21c3e3197da368ec71d2f8e33c51486b86ed8489ff47e1bc7ec7b2` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnorctl.yml` | `43c4654d8463660b30fe0ecc8abc38433a30caea1b8380a44785bd919aee5f0a` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/maintenance.yml` | `57bd737767e4a9c17155e64e1212dad67d3fa6f04338eaeee3a00c89a9944371` | `schedule.yml` | — |
| `.github/workflows/nightly.yml` | `8dea7ed56284644808077ef03154a961bb0bcad26422a85fa7524d69f63535d2` | `schedule.yml` | `actions/checkout`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/release.yml` | `1a4a391fd2b3cca5b0e7c9e105237fa65dfdbdbc22f08e26a658b1356f09d912` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `docker/setup-qemu-action`, `jdx/mise-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `mozilla-actions/sccache-action`, `rui314/setup-mold` |

## Source action mappings

| Source surface | Disposition | Fixture evidence or boundary |
| --- | --- | --- |
| `actions/attest-build-provenance` | `covered` | `l2-provenance.yml` |
| `actions/cache` | `covered` | `_rust-suite.yml` |
| `actions/cache/restore` | `covered` | `_rust-suite.yml` |
| `actions/cache/save` | `covered` | `_rust-suite.yml` |
| `actions/checkout` | `covered` | `_rust-suite.yml` |
| `actions/download-artifact` | `covered` | `_actions-suite.yml` |
| `actions/upload-artifact` | `covered` | `_actions-suite.yml` |
| `docker/build-push-action` | `covered` | `_docker-suite.yml` |
| `docker/login-action` | `covered` | `docker.yml`, `multi-arch.yml` |
| `docker/setup-buildx-action` | `covered` | `_docker-suite.yml` |
| `docker/setup-qemu-action` | `covered` | `_docker-suite.yml`, `multi-arch.yml` |
| `jdx/mise-action` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-bun-velnor.yml` | `covered` | `_runtime-suite.yml` |
| `local:./.github/workflows/ci-docker-docker.yml` | `covered` | `_docker-suite.yml` |
| `local:./.github/workflows/ci-docs-docs.yml` | `covered` | `pages.yml` |
| `local:./.github/workflows/ci-opentofu-opentofu.yml` | `hosted-only` | — — The fixture has no positive OpenTofu workflow lane yet. |
| `local:./.github/workflows/ci-release-package-signer.yml` | `external-admission-only` | — — Release package signing is a production mutation path; the fixture audits the workflow surface but does not execute the signer. |
| `local:./.github/workflows/ci-rust-policy.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-unit-collector.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-bench.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-client.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-control.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-model.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-render.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-runner.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-tools.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnor-workflow.yml` | `covered` | `_rust-suite.yml` |
| `local:./.github/workflows/ci-rust-velnorctl.yml` | `covered` | `_rust-suite.yml` |
| `mozilla-actions/sccache-action` | `covered` | `_rust-suite.yml` |
| `opentofu/setup-opentofu` | `hosted-only` | — — The fixture has no positive OpenTofu setup lane yet. |
| `oven-sh/setup-bun` | `hosted-only` | — — The fixture has no positive Bun setup lane yet. |
| `rui314/setup-mold` | `covered` | `_rust-suite.yml` |
| `taiki-e/install-action` | `hosted-only` | — — The fixture installs its Rust tools through its own pinned toolchain lane. |
| `tailrocks/velnor/.github/actions/setup-velnor-workflow` | `external-admission-only` | — — Base-owned Velnor workflow setup action is admitted on source workflows; the fixture executes its local pinned runtime setup instead. |
| `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` | `external-admission-only` | — — The policy workflow is a base-owned external reusable workflow; local policy structure is audited, not executed here. |

## Policy boundary

Customer `velnor-actions` reusable workflows, release mutation paths, and
base-owned Velnor setup/policy paths are admission or external-only surfaces.
The fixture workflows remain local and self-contained. Mandatory Linux positive
execution is dual-lane: GitHub-hosted Linux plus the configured Velnor Linux
lane. The checked-in capability and workflow audits bind this statement to the
exact source checkout and runner export under test.
