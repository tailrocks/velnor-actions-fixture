# Source Workflow Inventory

Current source inventory captured from Velnor `eafd266a151153b371d33357dcd34335719076ad`. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`eafd266a151153b371d33357dcd34335719076ad`](https://github.com/tailrocks/velnor/tree/eafd266a151153b371d33357dcd34335719076ad).
- Capability manifest: v13, runner crate `0.1.274`.
- Capability identity: `79a3a913b2e182b01ca2e40ea5478f7474bc5d5914957418581a2cd4c73cb785`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `6223eb75e0afb13f747443d4d8265ccd375eaa763fa1043e7965d0d687c4f201` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `oven-sh/setup-bun` |
| `.github/workflows/ci-docker-docker.yml` | `8a5dfd4fcbe6eb5a71b0b1275dcf6e5d4a6fbaa658c8d7885047cff5d409ce3a` | `_docker-suite.yml` | `actions/checkout`, `actions/download-artifact`, `crazy-max/ghaction-github-runtime`, `docker/setup-buildx-action` |
| `.github/workflows/ci-docs-docs.yml` | `34b36181647838eb42d07bf756689fe57203d1fe639cc7298288f8927ae653d3` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact` |
| `.github/workflows/ci-main.yml` | `478403299c9cc3e7eab3d996869630eee65f14379942d87e7549a7da7a35d9ff` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `7cf3a29a86b998b8fb2b9f3b5e8e9e1c39ebf99534ad909266473a4cc108b05c` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `opentofu/setup-opentofu` |
| `.github/workflows/ci-policy.yml` | `b204a65b0f6c480dc16390c274bc7fefb55c5a11ca65d401ef0efa23eff547bf` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `f38baff17fc64072516a561f029711dfcde168616b276b88e5260e2d50007941` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `63e76d5e5615192d52e34bba0b8bd51ddcec3b610e934633dd282c585d9721f1` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `4c132d96d4293b9fec7c787bec008c391dcfa40f9140232c43da090926d2bdcc` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-production-topology.yml` | `ec79a4c38085050506dcff2df8332e8b69e4da55d96e038449e8854fae7e8d63` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-unit-collector.yml` | `436956fc6f85b6672dc7464187e98db619ddd4ade56d2b49b0d508d070ccb2bc` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `ea0cc70a9d1243d163171b47e8a093fe86f903797d3bc1e74c04afcbf1aa1998` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-client.yml` | `7c28e82e32db2d8940807e29e7c6e826c32a6cc0adc04596def46424c647e01a` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-control.yml` | `f74cbe5bc0b2fca3ba6bcb39462fd97ad7d3a626e5ce1c73c9fda8ed5ef68889` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-model.yml` | `8f07c7577c7c4f09ad15152ad9dddec23a02f6f39a655ef0a2fa4347e48f1c56` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-render.yml` | `3f94c24f7790dd5aeadeffa2e32545f8df55211d16ffa261cdc5cd9005f5cabf` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `45fa67003b2546910c2153811376ca33926d24a24bce9668e67e1d5bf491c742` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `89bb51b203596878f6d8a343eeccdb646a91063d2c414d2083cb5b4bdcef4fae` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `d2c07f7b3cbf711efdab6e6c454a1d07d1f8e049238c5c59bfaceb90c33cc580` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/ci-rust-velnorctl.yml` | `d128cb9444e0e43166e527e11ecb579679b7bc5eb4a45703e7914effdee1c95d` | `_rust-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action` |
| `.github/workflows/maintenance.yml` | `0532765034745428f2c5c0905bad584c7adf4a9d883520622a83a94cf0180c3e` | `schedule.yml` | `actions/upload-artifact` |
| `.github/workflows/nightly.yml` | `c9bfef5909ab1334e7974ab6f3c485947382e52d44bbc89ff8f7cd5c5694fa71` | `schedule.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-production-topology.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/preview.yml` | `422114a540320684886dd90760ea3ff79f422fd7aac78046dae9b6c394091b94` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/release.yml` | `86da73802d929d5a36fdefe5787417d1f7537f4e26e2c490747724ad6082a68d` | `ci.yml` | `actions/cache`, `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/velnor-workflow-policy.yml` | `5f360c080d9aeb9ec00465979b44e7bfc43618363578fdf5518f48b136f2c8d2` | `ci.yml` | `actions/checkout`, `jdx/mr-boxington-action` |

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
