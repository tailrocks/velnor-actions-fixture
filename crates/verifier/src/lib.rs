//! The Velnor readiness verifier's oracle core.
//!
//! This crate exists because the fixture's previous evidence path could not
//! fail. Every compared field was a literal written in workflow YAML, so both
//! lanes emitted identical documents by construction, and normalization
//! dropped whole subtrees by key name at any depth. The types here make those
//! defects unrepresentable:
//!
//! - [`provenance`] collects run identity from the job environment and refuses
//!   to produce a record outside a real job.
//! - [`observe`] offers only collectors that measure something — exit statuses,
//!   files, environment effects, command files, GitHub-computed step outcomes.
//!   There is no collector for an authored literal.
//! - [`compare`] compares the observation subtree verbatim at every depth and
//!   normalizes only an explicit, closed, typed allowlist of provenance fields.
//! - [`record`] rejects evidence that lacks provenance, belongs to another run
//!   or commit, or was produced against a different Velnor build.

pub mod compare;
pub mod json;
pub mod observe;
pub mod provenance;
pub mod record;
