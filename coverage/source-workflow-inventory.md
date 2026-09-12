# Source Workflow Inventory

Current source inventory captured from Velnor `9c1a0782ec6138207986ee42016c0af1282ee02c`. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`9c1a0782ec6138207986ee42016c0af1282ee02c`](https://github.com/tailrocks/velnor/tree/9c1a0782ec6138207986ee42016c0af1282ee02c).
- Capability manifest: v13, runner crate `0.1.274`.
- Capability identity: `79a3a913b2e182b01ca2e40ea5478f7474bc5d5914957418581a2cd4c73cb785`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `2b4d29cb392f2367fd39172864f2fd65eb06aa8689c581ac865cdf4cd94ffccc` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `oven-sh/setup-bun` |
| `.github/workflows/ci-docker-docker.yml` | `1a353f5ae49d56e647dcaedcc8b5b9c045baf1899a55362e71dbea76a0de6027` | `_docker-suite.yml` | `actions/checkout`, `actions/download-artifact`, `crazy-max/ghaction-github-runtime`, `docker/setup-buildx-action` |
| `.github/workflows/ci-docs-docs.yml` | `d097fc71e1f4b3d34260795e99df086f55c66fbe0f515c3eb69be71c3ad1e4bd` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact` |
| `.github/workflows/ci-main.yml` | `d2237f87a39d4a82f8881b834ba24ae74f1469076bea5969862349716940086c` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `024c7ea5b4ed7480341a1f0f1c28e87788bf70f85fa7a5ef615f3f94b067e120` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `opentofu/setup-opentofu` |
| `.github/workflows/ci-policy.yml` | `b204a65b0f6c480dc16390c274bc7fefb55c5a11ca65d401ef0efa23eff547bf` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `39513c2ad5b98481706882f97382cc9a5b652c9f7578e06f879c4f85981d83f3` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `63e76d5e5615192d52e34bba0b8bd51ddcec3b610e934633dd282c585d9721f1` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `18c01862736858f2fd6f9918f047fdce75aad74614328a9652f411fe04688467` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-production-topology.yml` | `21d0b53675e08a0b8e8dcf904df0c1bddca1619fc96fa24c87a8fbe0f0bdf571` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-unit-collector.yml` | `90be0ad4da9e2b787ed68c84f3ca6eacc1657000bf873030586a470077b99483` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `5f8f8c1b58c1c569c576a9adebc2f54385103b5a6b9f7f5fc680d7357db4808b` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-client.yml` | `9e9bbd1fd844a58555fc1ebdd1fec04f59be209daa70e0db7102723c9ae0b485` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-control.yml` | `24ce2dae3f7ae218113017d4b8f54e4fdc2c569f2a8d329b33a20e7762a1b90a` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-model.yml` | `6e4a68286ceab6f0752e7c5b46115d01ad4d4db8e984d1b53483e54bd699dd56` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-render.yml` | `33a3575fbef4f7ead8f3b681b9c32aeea51297634828bb6afccab92bd1361fa9` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `69166f7b51857255b65bf4b69b1ecac4bc21df811b72932930135864d04c9ef7` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `3663f7d315bec1600b0abf8a83b5337b25462d321ec30df48facfb165b04d81b` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `de790db451156e975634baffaadd732f4cd44d0ef559bb2dae29ea77f06e2748` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnorctl.yml` | `0405ba41403e6e61390f311289b89d6973a18fda0d3373a61343b6ea5306db6b` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/maintenance.yml` | `ba5fef94b52fb31521ff44b170c8edfb723fe47187a1cf79c91f76d010f84d00` | `schedule.yml` | `actions/upload-artifact` |
| `.github/workflows/nightly.yml` | `412f4c617f1625b90341185a1e09b667036ac267f77c7069246e0b47e7b3042f` | `schedule.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/preview.yml` | `615bd8e6e7d43d38e2f6968ad2d201150d5ed3ac73ce67ca3cdaafd576510a69` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/release.yml` | `86da73802d929d5a36fdefe5787417d1f7537f4e26e2c490747724ad6082a68d` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/velnor-workflow-policy.yml` | `78a1fe789a20bc3568587ec831aea85d7fd18c04885ee632219b0180b454e72b` | `ci.yml` | `actions/checkout`, `jdx/mr-boxington-action` |

## Source action mappings

| Source surface | Disposition | Fixture evidence or boundary |
| --- | --- | --- |
| `actions/attest-build-provenance` | `covered` | l2-provenance.yml |
| `actions/cache` | `covered` | _rust-suite.yml |
| `actions/cache/restore` | `covered` | _rust-suite.yml |
| `actions/cache/save` | `covered` | _rust-suite.yml |
| `actions/checkout` | `covered` | _rust-suite.yml |
| `actions/download-artifact` | `covered` | _actions-suite.yml |
| `actions/upload-artifact` | `covered` | _actions-suite.yml |
| `crazy-max/ghaction-github-runtime` | `external-admission-only` | — — Velnor source workflow surface is admitted but not executed by this fixture. |
| `docker/build-push-action` | `covered` | _docker-suite.yml |
| `docker/login-action` | `covered` | docker.yml, multi-arch.yml |
| `docker/setup-buildx-action` | `covered` | _docker-suite.yml |
| `jdx/mise-action` | `covered` | _rust-suite.yml |
| `jdx/mr-boxington-action` | `external-admission-only` | — — Velnor source workflow surface is admitted but not executed by this fixture. |
| `local:./.github/workflows/ci-bun-velnor.yml` | `covered` | _runtime-suite.yml |
| `local:./.github/workflows/ci-docker-docker.yml` | `covered` | _docker-suite.yml |
| `local:./.github/workflows/ci-docs-docs.yml` | `covered` | pages.yml |
| `local:./.github/workflows/ci-opentofu-opentofu.yml` | `hosted-only` | — — The fixture has no positive OpenTofu workflow lane yet. |
| `local:./.github/workflows/ci-release-package-signer.yml` | `external-admission-only` | — — Release package signing is a production mutation path; the fixture audits the workflow surface but does not execute the signer. |
| `local:./.github/workflows/ci-rust-policy.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-production-topology.yml` | `external-admission-only` | — — Velnor source workflow surface is admitted but not executed by this fixture. |
| `local:./.github/workflows/ci-rust-unit-collector.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-bench.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-client.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-control.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-model.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-render.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-runner.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-tools.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnor-workflow.yml` | `covered` | _rust-suite.yml |
| `local:./.github/workflows/ci-rust-velnorctl.yml` | `covered` | _rust-suite.yml |
| `opentofu/setup-opentofu` | `hosted-only` | — — The fixture has no positive OpenTofu setup lane yet. |
| `oven-sh/setup-bun` | `hosted-only` | — — The fixture has no positive Bun setup lane yet. |
| `rui314/setup-mold` | `covered` | _rust-suite.yml |
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
