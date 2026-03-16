#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
use crate::types::*;

#[cfg(feature = "python")]
#[pymodule]
fn bioworkflow_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyTask>()?;
    Ok(())
}

#[cfg(feature = "python")]
#[pyclass(name = "Task")]
pub struct PyTask {
    pub inner: Task,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyTask {
    #[new]
    fn new(id: String, name: String) -> Self {
        Self {
            inner: Task::new(id, name),
        }
    }

    #[getter]
    fn id(&self) -> &str {
        &self.inner.id
    }

    #[getter]
    fn name(&self) -> &str {
        &self.inner.name
    }
}