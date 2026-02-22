//! DAG (Directed Acyclic Graph) engine for BioWorkflow
//!
//! Provides functionality for workflow parsing, DAG construction,
//! task scheduling, and execution management.

#![warn(missing_docs)]
#![deny(unsafe_code)]

pub mod builder;
pub mod executor;
pub mod parser;
pub mod scheduler;
pub mod visualization;

pub use builder::*;
pub use executor::*;
pub use parser::*;
pub use scheduler::*;
pub use visualization::*;
