# Source Workflow Inventory

Current source inventory captured from Velnor `de3f79fe2cb2d493e95023abfbbcd51a48d77346`. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`de3f79fe2cb2d493e95023abfbbcd51a48d77346`](https://github.com/tailrocks/velnor/tree/de3f79fe2cb2d493e95023abfbbcd51a48d77346).
- Capability manifest: v13, runner crate `0.1.267`.
- Capability identity: `9ead2d09e912d20d5e11318aa43012e3e61e4fba920d545697a73daacee84d0c`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `422274c4b36ebd35307895eab728ed1e89c1f73fd8b1f45861a7a78969c3aee8` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `oven-sh/setup-bun` |
| `.github/workflows/ci-docker-docker.yml` | `ece4584aef4045ec781bfdce0b1271455549652ee666b19c33eea1f6df3d2e0e` | `_docker-suite.yml` | `actions/checkout`, `actions/download-artifact`, `crazy-max/ghaction-github-runtime`, `docker/setup-buildx-action` |
| `.github/workflows/ci-docs-docs.yml` | `0aa9cc173746e55ad9f1d6fe9711bd258e07d345cf67d992e45c25f047fbb84b` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact` |
| `.github/workflows/ci-main.yml` | `fdda4fec30b1e25a44ae0adc7414f6fa27b25a523e2daf68fee8d028110c64f3` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `8c0ec60a3b558a1fa41ea6ad52e98b5b94f277696aa69cc7c861ff908e97030d` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `opentofu/setup-opentofu` |
| `.github/workflows/ci-policy.yml` | `b204a65b0f6c480dc16390c274bc7fefb55c5a11ca65d401ef0efa23eff547bf` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `70c0dd2a6f58a854f5c7110675dfa68060c92e23af4260249e8572a20fe2b2fa` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `f36e9448c9b40b4ca00a8d2cadb65cce5b2ada5f076fc9ba493e58ea7ca69e66` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `c49461f8946a8471d08171649b7d876f5a5c71c4e5d7e29775e27b3d0948ed25` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-production-topology.yml` | `9feeec1cb11c93f1069076802b351e06d3470657fb273792720aa8fc6544ebd1` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-unit-collector.yml` | `921c34141ec76798f926c8504a26aa150f590504c661d2055fb8d22c20d29da5` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `610cd73bc741ded84f389e7b6c603ebf8d1c4f613ccc006e0d6b614a53addf50` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-client.yml` | `e3957e57e16862d74974d41f07c616520723fca24617d6a0c063ca6b4c8e9c0f` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-control.yml` | `76a17684a1702076861f51abbecda8106c989dd6a8a020b6487c10eb8802a98c` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-model.yml` | `bf49c1ac46733438df704d23dc1c35ed652912f71e00d083bb55bd6a66cee9f9` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-render.yml` | `b81d6fb6697512f210c9753c4af4837e70c1ca9c3adf86a66d2b3130179fd6f0` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `e379a3a87bcb39c5d07bdac148cb10479ed6458718c2074a5206b0ba946c35be` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `110149b965129e0821bf5e3686dceee33a279b3c526dc71986f7a780626ad485` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `6f8dcce4fb68d76215ce7ae0969056f02234b31b447da47cecacda22441c20cc` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/ci-rust-velnorctl.yml` | `92f10656579ca3ccd70790f2b962673ef313c297a56fcf5c893391d9b12cd9ac` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold` |
| `.github/workflows/maintenance.yml` | `d63e614736806cabbc4829d8d0562c4e8879dc35c7cc5df8fd298bf9a9487e3b` | `schedule.yml` | `actions/upload-artifact` |
| `.github/workflows/nightly.yml` | `abec820c14ca516eaabc88d4c7e8cf0507bb8049589ba0cdb4a6e0f3a63c0aa4` | `schedule.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/release.yml` | `86da73802d929d5a36fdefe5787417d1f7537f4e26e2c490747724ad6082a68d` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/velnor-workflow-policy.yml` | `af0d7fe0fae080bef0470db391efb0b165a0f68a9e86af760db5582a6b60b365` | `ci.yml` | `actions/checkout`, `jdx/mr-boxington-action` |

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
