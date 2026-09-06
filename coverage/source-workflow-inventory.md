# Source Workflow Inventory

Current source inventory captured from Velnor **d2063fbb0a9d676d92ed7072e5ec521e1279989c**. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`d2063fbb0a9d676d92ed7072e5ec521e1279989c`](https://github.com/tailrocks/velnor/tree/d2063fbb0a9d676d92ed7072e5ec521e1279989c).
- Capability manifest: v13, runner crate `0.1.258`.
- Capability identity: `eb68a1df1a3f83d97c91cdba38211b3c9f22bbda5fc4b80531db154a1f5bb74a`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `dbb5cd1fdde36342837b225bf50bc6033dea908e67da6d6c4500e030188b4832` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `oven-sh/setup-bun` |
| `.github/workflows/ci-docker-docker.yml` | `d75a177be201ae2c5e2a8c45af1d1835f3879f1109928655f69380cd69decf23` | `_docker-suite.yml` | `actions/checkout`, `actions/download-artifact`, `crazy-max/ghaction-github-runtime`, `docker/setup-buildx-action` |
| `.github/workflows/ci-docs-docs.yml` | `4c9f2ecf130841f62167e2bf919eea44c5e4b3e73115442062baee159f52742a` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact` |
| `.github/workflows/ci-main.yml` | `ee49ebd3ce743f4acff122bc2b6bedc4e94668b09d8bfda422027b0d9e1a1c85` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `c8adfba06fbf15a85f3598a5ddde795c127f0273f3447fbbb238278f7cc2ceed` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `opentofu/setup-opentofu` |
| `.github/workflows/ci-policy.yml` | `d2713b89626fd7df397a9ac3773ed2e0c08c5cdf2674bfadf1dc8c9968ee928d` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `10af5a0330ea5803a6981b9ee7086fcf1c73eb7ba1148592af9e8fb9bb4ea0f7` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `f36e9448c9b40b4ca00a8d2cadb65cce5b2ada5f076fc9ba493e58ea7ca69e66` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `c50ccd8d6e4b150b8ff44f49f2ea394295488a0c52d7b7554c71cd3c1e19e285` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-unit-collector.yml` | `957150ec603343fe178e9714f53cace128e1a506057bc8608c87c14995b406b9` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `c4a990785c000ca52a7c8ea90b6d9e961c6046321e846727c888b70855705774` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-client.yml` | `cdd3950270113bd00ef6d7c730365c4ff8726f4350cd493ec98625c74cda86ad` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-control.yml` | `bd0c1c0198741c14e29c5f006b06aad394bc73ed040327444a60f1acd432afbd` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-model.yml` | `b776782f11193fd07f8984971909be79d3b05c46c9ccb50af94295df6ce1b3fb` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-render.yml` | `69cf56f8772eebb030f533302f1993c898846395d63fc4f8869324dedbbc9db5` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `01b512b8f84b9021018ee1c92f38e275fccf018115859a1b573564e231de4a2a` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `7ceb2ebd81a9c75414e81d8445662cf90cf20fced1dd44212b02403ea21728c7` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `99a0a6c7d498c2721d49cf6fc652a75e9386165c049fab44b58c34d18d78944e` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnorctl.yml` | `9b41f0c8577821c200bd530c9c77ad7d386e763db2de65338f424218a5435788` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/maintenance.yml` | `57bd737767e4a9c17155e64e1212dad67d3fa6f04338eaeee3a00c89a9944371` | `schedule.yml` | — |
| `.github/workflows/nightly.yml` | `8ddd9d52c014a2b311ae9eea4a48eecad7e9c5a81b670d1313321ad62bdb9c1a` | `schedule.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/release.yml` | `cc1560563cb739e4ed55390c9de6ce86adc6f83a5158ec50e0ef9a45c730359a` | `ci.yml` | `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `crazy-max/ghaction-github-runtime`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `docker/setup-qemu-action`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/velnor-workflow-policy.yml` | `52fb9fe6fee4fd20785b9208abcec606be16cf38fe60f479a80fa4b435e54dfa` | `ci.yml` | `actions/checkout`, `jdx/mr-boxington-action` |

## Source action mappings

| Source surface | Disposition | Fixture evidence or boundary |
| --- | --- | --- |
| `actions/attest-build-provenance` | `covered` | `l2-provenance.yml` |
| `actions/cache/restore` | `covered` | `_rust-suite.yml` |
| `actions/cache/save` | `covered` | `_rust-suite.yml` |
| `actions/checkout` | `covered` | `_rust-suite.yml` |
| `actions/download-artifact` | `covered` | `_actions-suite.yml` |
| `actions/upload-artifact` | `covered` | `_actions-suite.yml` |
| `crazy-max/ghaction-github-runtime` | `external-admission-only` | — — Velnor source workflow surface is admitted but not executed by this fixture. |
| `docker/build-push-action` | `covered` | `_docker-suite.yml` |
| `docker/login-action` | `covered` | `docker.yml`, `multi-arch.yml` |
| `docker/setup-buildx-action` | `covered` | `_docker-suite.yml` |
| `docker/setup-qemu-action` | `covered` | `_docker-suite.yml`, `multi-arch.yml` |
| `jdx/mise-action` | `covered` | `_rust-suite.yml` |
| `jdx/mr-boxington-action` | `external-admission-only` | — — Velnor source workflow surface is admitted but not executed by this fixture. |
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
| `opentofu/setup-opentofu` | `hosted-only` | — — The fixture has no positive OpenTofu setup lane yet. |
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
