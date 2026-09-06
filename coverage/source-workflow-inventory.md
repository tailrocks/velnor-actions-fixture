# Source Workflow Inventory

Current source inventory captured from Velnor **08376a8d65baf36f7bafaa662b02c5e26a601873**. The JSON
contract and this document are regenerated together whenever the target Velnor
source changes; readiness rejects a stale source digest, workflow hash, action
surface, or mapping.

## Scan basis

- Velnor source: [`08376a8d65baf36f7bafaa662b02c5e26a601873`](https://github.com/tailrocks/velnor/tree/08376a8d65baf36f7bafaa662b02c5e26a601873).
- Capability manifest: v13, runner crate `0.1.258`.
- Capability identity: `eb68a1df1a3f83d97c91cdba38211b3c9f22bbda5fc4b80531db154a1f5bb74a`.
- Runner scope: Linux jobs through Docker and the GitHub V2 JIT flow. macOS,
  native scheduling, and production release mutation remain admission surfaces.

## Velnor workflow inventory

| Source workflow | SHA-256 | Fixture mapping | Source action/reusable-workflow surfaces |
| --- | --- | --- | --- |
| `.github/workflows/ci-bun-velnor.yml` | `f04e525972fcf07b76fc75623da555047baeb8a29199166686390efaa5374f25` | `_runtime-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `oven-sh/setup-bun` |
| `.github/workflows/ci-docker-docker.yml` | `1f93a768a379fc8758385502414d7da5fdba1a27fb865c00d880e18c7711ae19` | `_docker-suite.yml` | `actions/checkout`, `actions/download-artifact`, `crazy-max/ghaction-github-runtime`, `docker/setup-buildx-action` |
| `.github/workflows/ci-docs-docs.yml` | `4522a6931797ebb70e3c89069d329e3fc383ae5804fc0ebbf6fe4b1e04918d0d` | `pages.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact` |
| `.github/workflows/ci-main.yml` | `c1ea1891e8f765ca4a61be820d1eb31007bf00e3cd1bf55ba1f23eee8d6ef57c` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-opentofu-opentofu.yml` | `301cb090de74a1a3a65388561065431f36b9409c95ca5dbdb816046be426229a` | `_docker-suite.yml` | `actions/cache/restore`, `actions/cache/save`, `actions/checkout`, `actions/download-artifact`, `opentofu/setup-opentofu` |
| `.github/workflows/ci-policy.yml` | `b886a80a66f307e333e8e585673690ace8ecf486f2d0e062d1ab1bd3430d8c9d` | `ci.yml` | `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/ci-pr.yml` | `e0e0b31b43b13120faa50f124a2377097fee5a092be9d5d1e6bc1269ea64e480` | `ci.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow` |
| `.github/workflows/ci-release-package-signer.yml` | `f36e9448c9b40b4ca00a8d2cadb65cce5b2ada5f076fc9ba493e58ea7ca69e66` | `ci.yml` | `actions/attest-build-provenance`, `actions/download-artifact` |
| `.github/workflows/ci-rust-policy.yml` | `2747aad2c157654648057ef9e002c41addc859ea5556c20a6d1c77d8a65c5fb1` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-unit-collector.yml` | `b1ff86e6f1de193a1fee5dcb1ea7f01e0d87a10bfc880cfa0e88e35607556f5b` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-bench.yml` | `7a25c8b135012b3513c50a1b9979f127f28e487e42c51ba64148b484b4175322` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-client.yml` | `d324b1f1e168a4753f98fc6eb997374644895fdc27cee2858c04952e745f0e2a` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-control.yml` | `585da36466e589798678d958208c0bcf9a906503169bfef4433b45a59d6edf20` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-model.yml` | `a717cc11ae1a23d9e0efe53278fbb95c745a5bb610ddea59baa8ade2218c015c` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-render.yml` | `61e988bd60fe3938b89f1726a957f0917e70893136858850103786ab13c26341` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-runner.yml` | `340a095f750ca1c9e78490e6fed977ad0b54321d577cbbc8aaa69b3132992868` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-tools.yml` | `7cfaceefe4d0bab9c07377a3a8bb26b61378b5c890f3e69c556a1bc89c99dd77` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnor-workflow.yml` | `1facb2e592beceaabd3e49d66d48b1ef3e2bd862388fa3f088cfe7f9b95e9f35` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/ci-rust-velnorctl.yml` | `5afae9fd7716c184ed9ce2d92af2fec95a7459f85c6bd348884c0f4da1b93904` | `_rust-suite.yml` | `actions/checkout`, `actions/download-artifact`, `jdx/mise-action`, `jdx/mr-boxington-action`, `rui314/setup-mold`, `taiki-e/install-action` |
| `.github/workflows/maintenance.yml` | `57bd737767e4a9c17155e64e1212dad67d3fa6f04338eaeee3a00c89a9944371` | `schedule.yml` | — |
| `.github/workflows/nightly.yml` | `53def0ee3a9c5dfbdf0fc29f4d335bccebcf517eac6b91a4a9f48f1ec0055617` | `schedule.yml` | `actions/checkout`, `actions/upload-artifact`, `local:./.github/workflows/ci-bun-velnor.yml`, `local:./.github/workflows/ci-docker-docker.yml`, `local:./.github/workflows/ci-docs-docs.yml`, `local:./.github/workflows/ci-opentofu-opentofu.yml`, `local:./.github/workflows/ci-rust-policy.yml`, `local:./.github/workflows/ci-rust-unit-collector.yml`, `local:./.github/workflows/ci-rust-velnor-bench.yml`, `local:./.github/workflows/ci-rust-velnor-client.yml`, `local:./.github/workflows/ci-rust-velnor-control.yml`, `local:./.github/workflows/ci-rust-velnor-model.yml`, `local:./.github/workflows/ci-rust-velnor-render.yml`, `local:./.github/workflows/ci-rust-velnor-runner.yml`, `local:./.github/workflows/ci-rust-velnor-tools.yml`, `local:./.github/workflows/ci-rust-velnor-workflow.yml`, `local:./.github/workflows/ci-rust-velnorctl.yml`, `tailrocks/velnor/.github/actions/setup-velnor-workflow`, `tailrocks/velnor/.github/workflows/velnor-workflow-policy.yml` |
| `.github/workflows/release.yml` | `cc1560563cb739e4ed55390c9de6ce86adc6f83a5158ec50e0ef9a45c730359a` | `ci.yml` | `actions/checkout`, `actions/download-artifact`, `actions/upload-artifact`, `crazy-max/ghaction-github-runtime`, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `docker/setup-qemu-action`, `jdx/mise-action`, `jdx/mr-boxington-action`, `local:./.github/workflows/ci-release-package-signer.yml`, `rui314/setup-mold` |
| `.github/workflows/velnor-workflow-policy.yml` | `59addb12e43b9543afd08d015f2ff53dcdd5b22b7969e2d1605b3018bf0f3001` | `ci.yml` | `actions/checkout`, `jdx/mr-boxington-action` |
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
