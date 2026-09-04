# Source Workflow Inventory

Source inventory synchronized: **2026-09-04**. This inventory records the
workflow surfaces used to scope fixture coverage.

## Scan basis

- Velnor was synchronized at commit
  [`3fa9e40916555e4c0b61512cceeb5a179f561c9d`](https://github.com/tailrocks/velnor/tree/3fa9e40916555e4c0b61512cceeb5a179f561c9d).
- The capability baseline is manifest v12, with source identity
  [`3fa9e40916555e4c0b61512cceeb5a179f561c9d`](https://github.com/tailrocks/velnor/tree/3fa9e40916555e4c0b61512cceeb5a179f561c9d).
- Runner scope is Linux jobs through Docker and the GitHub V2 JIT flow. It
  includes no macOS job execution and no native scheduler surface.
- This was a read-only source scan. It does not claim live runner execution;
  live validation requires credentials and a configured Velnor runner.

## Velnor main workflow inventory

At the source commit above, `.github/workflows` contains exactly these four
workflow files:

| Workflow | Current source surfaces | Fixture mapping |
| --- | --- | --- |
| `ci.yml` | Pull request, `main`/tag push, `merge_group`, weekly schedule, and manual `lanes` plus recovery/benchmark/cache-proof inputs; three owner-gated server-side `velnor-actions` `ci-code.yml` calls; `ci-required` runs on `ubuntu-26.04` or `self-hosted,velnor-target-mvp`. | Local `ci.yml` preserves the dual-lane contract and maps execution to `_rust-suite.yml`, `_runtime-suite.yml`, `_actions-suite.yml`, `_docker-suite.yml`, `l2-runtime.yml`, and `l2-provenance.yml`; the external `ci-code.yml` calls remain admission-only. |
| `guest-image.yml` | Pull requests scoped to `microvm/**` and guest-image sources, manual `lanes`, and `v*` tag push; fail-closed lane admission; x86_64/amd64 and aarch64/arm64 guest kernel/rootfs matrix; checkout, mise, sccache, cache, guest-agent embedding, and artifact upload. | No positive local guest-image build is claimed. `backend-parity.yml` and `control-plane.yml` record the microVM expected-unsupported boundary; the missing user-namespace/CAP_SYS_ADMIN capability is an explicit negative disposition. |
| `release.yml` | `v*` tag push and manual `lanes`/`tag`; identity and final default-branch/tag gates; amd64/arm64 guest images, OCI image, runner tarballs/debs, checksums, release record/publication, and four hosted package-signer calls at `tailrocks/velnor-actions@2d045521be342284cd567b7058a0e635dc74b37c`. | Local `docker.yml`, `multi-arch.yml`, `_docker-suite.yml`, and `l2-provenance.yml` cover the build, artifact, image, and provenance surfaces. Release mutation and hosted package signing stay external-admission-only; no local workflow executes the signer. |
| `renovate.yml` | Weekly schedule and manual `lanes`; Velnor/GitHub writer/read-only matrix; checkout, cache, and `renovatebot/github-action`. | Local `renovate.yml` mirrors the writer/read-only matrix and admits the action surface; mutation remains lane-controlled. |

The source workflow action identities are immutable pins. `ci.yml` calls
`jackin-project/velnor-actions/.github/workflows/ci-code.yml@796dfcd26d4110319c8363155d2eae6885114893`,
`tailrocks/velnor-actions/.github/workflows/ci-code.yml@c222e52030fee9ea6eae573a5769770be01d8438`,
and
`ChainArgos/velnor-actions/.github/workflows/ci-code.yml@77173e8e71aa18e60d21f9f0d1ae57c0695d0233`.
`guest-image.yml` uses checkout
`3d3c42e5aac5ba805825da76410c181273ba90b1`, mise
`c2a87611a18de5b3828c5652fe268e992400cb5c`, sccache
`fc920bf0ec8de6ee65d409111f7ec508035751ba`, cache
`55cc8345863c7cc4c66a329aec7e433d2d1c52a9`, and upload-artifact
`043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`. `release.yml` additionally uses
mold `7e4f20ad28a2e8ca6fd0892ccf72e2abb706b9c3`, download-artifact
`3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`, QEMU
`96fe6ef7f33517b61c61be40b68a1882f3264fb8`, Buildx
`37fe631027851001ddb9b187196cc803df7f5f0e`, Docker login
`dbcb813823bdd20940b903addbd779551569679f`, and Docker build/push
`53b7df96c91f9c12dcc8a07bcb9ccacbed38856a`; Renovate uses
`5402b206248e5a8c8427a15102702eb9c1793efc`. The JSON contract retains every
full SHA, input, and subpath admitted by manifest v12.

## Source revisions

The workflow inventories below were read from these `main` commits:

| Repository | Commit |
| --- | --- |
| `ChainArgos/java-monorepo` | `81c4fa7aeef59c32f3db32155a2c551382523870` |
| `jackin-project/jackin` | `5ae68cd88d0f76a421b0331be4357ba20f657261` |
| `jackin-project/homebrew-tap` | `f7f45ce8fab4ef2110c6844fc49c9a8f8aeaf95d` |
| `jackin-project/jackin-the-architect` | `29e0e600b395195f5fa1bc3c70ea585cfe7518d3` |
| `tailrocks/ruxel` | `779d4b9d514ea36315d715da5461f9789e981e97` |
| `tailrocks/holla` | `d22455109ba442fd72a73a8b0a9563d74b6f251d` |
| `tailrocks/termrock` | `35dddcf49bb2b3ef6d08776c337788df20ec2a33` |
| `tailrocks/parallax` | `e55207c21e23c043cc989c9327491545ffcc611b` |
| `tailrocks/tablerock` | `f61e3f8d26b6d654d7eb51ad8614157f4cc99234` |
| `tailrocks/schemalane` | `6962a6411f82601a85ae8ccfccfe2e8cd066aac0` |

## Exact workflow filename inventories

- [`ChainArgos/java-monorepo` workflow tree](https://github.com/ChainArgos/java-monorepo/tree/main/.github/workflows): `ansible.yml`, `ci.yml`, `kestra-build-publish.yml`, `renovate.yml`, `rust-docker.yml`.
- [`jackin-project/jackin` workflow tree](https://github.com/jackin-project/jackin/tree/main/.github/workflows): `cache-cleanup.yml`, `ci.yml`, `construct-public-unmerged.yml`, `construct.yml`, `desktop-cadence.yml`, `docs-public-unmerged.yml`, `docs.yml`, `hygiene.yml`, `jackin-dev-public-unmerged.yml`, `jackin-dev.yml`, `preview.yml`, `release.yml`, `renovate-validate-public-unmerged.yml`, `renovate-validate.yml`, `renovate.yml`, `reuse-compliance-public-unmerged.yml`, `reuse-compliance.yml`, `rust-nextest.yml`.
- [`jackin-project/homebrew-tap` workflow tree](https://github.com/jackin-project/homebrew-tap/tree/main/.github/workflows): `cask-validation.yml`, `ci.yml`, `package-update.yml`, `reuse-compliance-public-unmerged.yml`, `reuse-compliance.yml`.
- [`jackin-project/jackin-the-architect` workflow tree](https://github.com/jackin-project/jackin-the-architect/tree/main/.github/workflows): `ci.yml`, `gitleaks-history.yml`, `jackin-toolchain.yml`, `precommit-public-unmerged.yml`, `precommit.yml`, `publish-image.yml`, `renovate.yml`, `reuse-compliance-public-unmerged.yml`, `reuse-compliance.yml`.
- [`tailrocks/ruxel` workflow tree](https://github.com/tailrocks/ruxel/tree/main/.github/workflows): `ci.yml`, `preview.yml`, `release.yml`.
- [`tailrocks/holla` workflow tree](https://github.com/tailrocks/holla/tree/main/.github/workflows): `ci.yml`, `preview.yml`, `release-deb.yml`, `release.yml`, `renovate.yml`.
- [`tailrocks/termrock` workflow tree](https://github.com/tailrocks/termrock/tree/main/.github/workflows): `ci.yml`, `docs.yml`, `hygiene.yml`, `release.yml`.
- [`tailrocks/parallax` workflow tree](https://github.com/tailrocks/parallax/tree/main/.github/workflows): `ci.yml`, `dependency-discovery.yml`, `footprint.yml`, `mcp-evals.yml`, `preview.yml`, `release.yml`, `scheduled-measurement.yml`, `storage-integration.yml`, `upgrade-harness.yml`.
- [`tailrocks/tablerock` workflow tree](https://github.com/tailrocks/tablerock/tree/main/.github/workflows): `ci.yml`, `native-nightly.yml`, `native-release.yml`, `native.yml`, `package-release.yml`, `preview.yml`.
- [`tailrocks/schemalane` workflow tree](https://github.com/tailrocks/schemalane/tree/main/.github/workflows): `ci.yml`, `release.yml`.

## Common observed surfaces

The scan observed PR, push, tag, `merge_group`, schedule, and manual
(`workflow_dispatch`) triggers; `ubuntu-26.04`, self-hosted
`velnor-target-mvp`, and `macos-26` runner labels; matrices and concurrency;
checkout, cache, mise, sccache, and mold; artifacts; Docker Buildx, bake,
login, and metadata; Pages; releases and Homebrew; attestations; Renovate;
secrets; and both local and remote reusable workflows.

## Fixture mapping

| Source surface | Fixture coverage |
| --- | --- |
| Rust build/test workflows | `_rust-suite` plus Rust examples/tests cover fmt, clippy, check, nextest, cache, and sccache. |
| Runtime orchestration | `_runtime-suite` covers command files, `needs`, matrices, and artifacts. |
| Action adapters | `_actions-suite` covers action adapters and the expected microVM-unsupported result. |
| Docker workloads | `_docker-suite`, `docker`, and `multi-arch` cover Buildx and containers. |
| Pages | `pages.yml` provides Pages parity. |
| L2 behavior | `l2-runtime.yml`, `l2-provenance.yml`, and `l2-negative.yml` cover closure, provenance, and negative paths. |
| Control plane | `control-plane.yml` covers success, failure, hold, queue, concurrent runs, artifacts, cache, and load. |
| Compatibility | `compat.yml` and its public-unmerged counterpart cover cache/backend compatibility. |

## Policy boundary

Customer `velnor-actions` reusable workflows, mutation/release paths, and
macOS paths are admission/exception surfaces, not runtime dependencies. The
fixture must keep its workflows local. Only mandatory Linux positive execution
is dual-lane: GitHub-hosted Linux plus the configured Velnor Linux lane.

## Source documentation

- [Velnor runner usage](https://github.com/tailrocks/velnor/blob/3fa9e40916555e4c0b61512cceeb5a179f561c9d/docs/runner-usage.md)
- [Velnor target live runbook](https://github.com/tailrocks/velnor/blob/3fa9e40916555e4c0b61512cceeb5a179f561c9d/docs/target-live-runbook.md)
- [Velnor roadmap and host/job scope](https://github.com/tailrocks/velnor/blob/3fa9e40916555e4c0b61512cceeb5a179f561c9d/docs/roadmap.md)
