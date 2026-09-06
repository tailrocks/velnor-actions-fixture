# Source Workflow Inventory

Current source inventory captured from Velnor ``5491f677093d07855143f8da9640ce18c55d83cf``. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`5491f677093d07855143f8da9640ce18c55d83cf`](https://github.com/tailrocks/velnor/tree/5491f677093d07855143f8da9640ce18c55d83cf).
- Capability manifest: v12, runner crate `0.1.261`.
- Capability identity: `7afe8dcd85e8a501f00925e533e64ea795fe321d56294adcb845b9272965390c`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `e01aa22e84f3c8c19f3b6dd2df846800ad981b05c2e59ddf9c5d1a1ab8b447e0` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `oven-sh/setup-bun`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-docker-docker.yml` | `6a7a339ff0169b3a34eb4204624e82589df8eb115e98b08721baf69cf43e8fad` | `_docker-suite.yml` | `actions/checkout`, `docker/setup-buildx-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-docs-docs.yml` | `f3d0500e0de8f30cf36849367d3d8ccf8f7e5621a9f767a7f2a5d324e0399f48` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-main.yml` | `71c2bf0913ae2030a5358e1fa071957b825eee9d86b0c1bcdccd47ae0c6c2130` | `ci.yml` | `actions/checkout`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `79dd0e0d631c145cbe8f9e1f6a6552a561348b311b0a7855b7f1801452d0d1c9` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `opentofu/setup-opentofu`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-policy.yml` | `91d810cbed000b32d3cba2a4879181fe71439136a3486ba969d50c2130593416` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `cbf077b35a185eca539bdadf15aa7b2b129a0d4f9da15fc2d98a78680196047d` | `ci.yml` | `actions/checkout`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `f33d962f452406f20144f3d9b8f1c3fc209b5a09863ff4c064a65c2c243055a1` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `0361df131d32833a336a5bdb0f68b3001bedcf85a4b5e6deee9bc37520f311e5` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-unit-collector.yml` | `2b105feaeccb7fe4334edbb812e5ea36ff0ecbe4dafb65c2097c88540e01951b` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `50d95cf301dbb6690d0367d83d676e4dd47e614b329acc48ccc3503540c88d9f` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-client.yml` | `1e9d0b99285e0ee7175fffca90feb537ceecc8a848e7fb26e0f27e0f62873b9e` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-control.yml` | `4d7f6cfa30ef54a6d5cd4e17e8e26b299ac4b65135bb7fd26d1bd34d3ec1dbf0` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-model.yml` | `7c4da9c51c3a15eeceffe2c3abf6fa8edb21cd3b43dac140b9162d094e9d1533` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-render.yml` | `15db887b4fad53e636b5b5a144bcf85bf2fc5b6be87e7cfa868cf8dff7d4153d` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `db53c1b28fa7b38287ed9153c832cc0ab622c2cee041ba97a4a49768dd06ad8b` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `86cfa3fe91aa000cfc4a345b3e586e0d9b3128732657680b3ab8955432e7a757` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `eb31c411cd89b3dba158f6497357f4447e7ab4912b688e23c6ff01bac5ca1ebf` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-rust-velnorctl.yml` | `4d98c32f1a89b85b87fc291bfeb1f8e0e0afecf162e732c3e88fe7ea2916583e` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `jdx/mise-action`, `mozilla-actions/sccache-action`, `rui314/setup-mold`, `taiki-e/install-action`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/maintenance.yml` | `57bd737767e4a9c17155e64e1212dad67d3fa6f04338eaeee3a00c89a9944371` | `schedule.yml` | — |
| `.github/workflows/nightly.yml` | `3a87a229506a67015dd6ab570b11289b2adb6e32b0644a3d275d223f6022ee38` | `schedule.yml` | `actions/checkout`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/velnor-workflow-policy.yml` | `abc4b1fc54fef3cd7ea99fa709de32e9d0ae84601befe9e22e9fc96cadbd83a2` | `ci.yml` | `actions/checkout` |
| `.github/workflows/release.yml` | `a8b4559beb5165b504b1b2bf37599ac4618a547593d6eebccfbac5b1d96d7761` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `jdx/mise-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `mozilla-actions/sccache-action`, `rui314/setup-mold` |

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
| `opentofu/setup-opentofu` | `hosted-only` | — — The fixture has no positive OpenTofu workflow lane yet. |
| `oven-sh/setup-bun` | `hosted-only` | — — The fixture has no positive Bun setup lane yet. |
| `rui314/setup-mold` | `covered` | `_rust-suite.yml` |
| `taiki-e/install-action` | `hosted-only` | — — The fixture installs its Rust tools through its own pinned toolchain lane. |
| `tailrocks/velnor/.github/actions/setup-velnor-workflow` | `external-admission-only` | — — Base-owned Velnor workflow setup action is admitted on source workflows; the fixture executes its local pinned runtime setup instead. |
| `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` | `external-admission-only` | — — The policy workflow is a base-owned external reusable workflow; local policy structure is audited, not executed here. |

## Policy boundary

Retired external reusable workflows, release mutation paths, and base-owned
Velnor setup/policy paths are admission or external-only surfaces. The fixture
workflows remain local and self-contained. Mandatory Linux positive execution
is dual-lane: GitHub-hosted Linux plus the configured Velnor Linux lane. The
checked-in capability and workflow audits bind this statement to the exact
source checkout and runner export under test.
