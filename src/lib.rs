use boxcars::NetworkParse;
use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use serde_json::Value;

#[pyfunction]
fn parse_replay(data: &[u8]) -> PyResult<PyObject> {
    let replay = boxcars::ParserBuilder::new(data)
        .with_network_parse(NetworkParse::IgnoreOnError)
        .on_error_check_crc()
        .parse()
        .map_err(to_py_error)?;
    
    let replay = serde_json::to_value(replay).map_err(to_py_error)?;
    
    Python::with_gil(|py| {
        let replay = convert_to_py(py, &replay);
        Ok(replay)
    })
}

#[pymodule]
fn _lib(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_replay, m)?)?;
    Ok(())
}

fn to_py_error<E: std::error::Error>(e: E) -> PyErr {
    PyException::new_err(format!("Boxcars parsing error: {}", e))
}

fn convert_to_py(py: Python, value: &Value) -> PyObject {
    match value {
        Value::Null => py.None(),
        Value::Bool(b) => b.into_py(py),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                i.into_py(py)
            } else if let Some(u) = n.as_u64() {
                u.into_py(py)
            } else if let Some(f) = n.as_f64() {
                f.into_py(py)
            } else {
                py.None()
            }
        },
        Value::String(s) => s.into_py(py),
        Value::Array(list) => {
            let list: Vec<PyObject> = list.iter().map(|e| convert_to_py(py, e)).collect();
            list.into_py(py)
        },
        Value::Object(m) => {
            let dict = pyo3::types::PyDict::new_bound(py);
            for (k, v) in m {
                dict.set_item(k, convert_to_py(py, v)).unwrap();
            }
            dict.into_py(py)
        },
    }
}
