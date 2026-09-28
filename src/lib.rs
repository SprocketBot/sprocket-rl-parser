use boxcars::NetworkParse;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::IntoPyObjectExt;
use serde_json::Value;

#[pyfunction]
fn parse_replay(py: Python<'_>, data: &[u8]) -> PyResult<Py<PyAny>> {
    let replay = boxcars::ParserBuilder::new(data)
        .with_network_parse(NetworkParse::IgnoreOnError)
        .on_error_check_crc()
        .parse()
        .map_err(to_py_error)?;

    let replay = serde_json::to_value(replay).map_err(to_py_error)?;

    convert_to_py(py, &replay)
}

#[pyfunction]
fn parse_replay_header_only(py: Python<'_>, data: &[u8]) -> PyResult<Py<PyAny>> {
    let replay = boxcars::ParserBuilder::new(data)
        .with_network_parse(NetworkParse::Never)
        .on_error_check_crc()
        .parse()
        .map_err(to_py_error)?;

    let replay = serde_json::to_value(replay).map_err(to_py_error)?;

    convert_to_py(py, &replay)
}

#[pymodule]
fn _lib(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_replay, m)?)?;
    m.add_function(wrap_pyfunction!(parse_replay_header_only, m)?)?;
    Ok(())
}

fn to_py_error<E: std::error::Error>(e: E) -> PyErr {
    PyException::new_err(format!("Boxcars parsing error: {}", e))
}

fn convert_to_py(py: Python<'_>, value: &Value) -> PyResult<Py<PyAny>> {
    match value {
        Value::Null => Ok(py.None()),
        Value::Bool(b) => b.into_py_any(py),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                i.into_py_any(py)
            } else if let Some(u) = n.as_u64() {
                u.into_py_any(py)
            } else if let Some(f) = n.as_f64() {
                f.into_py_any(py)
            } else {
                Ok(py.None())
            }
        }
        Value::String(s) => s.into_py_any(py),
        Value::Array(list) => {
            let list: Vec<Py<PyAny>> = list
                .iter()
                .map(|e| convert_to_py(py, e))
                .collect::<PyResult<_>>()?;
            list.into_py_any(py)
        }
        Value::Object(m) => {
            let dict = PyDict::new(py);
            for (k, v) in m {
                dict.set_item(k, convert_to_py(py, v)?)?;
            }
            Ok(dict.into_any().unbind())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyBool, PyFloat, PyInt, PyList, PyString};
    use serde_json::json;

    #[test]
    fn converts_nested_json_to_native_python_types() {
        Python::initialize();
        Python::attach(|py| {
            let value = json!({
                "values": [null, true, false, i64::MIN, u64::MAX, 1.5, "🚀"],
                "empty_list": [],
                "empty_object": {}
            });
            let converted = convert_to_py(py, &value).unwrap();
            let dict = converted.bind(py).cast::<PyDict>().unwrap();
            let values = dict.get_item("values").unwrap().unwrap();
            let values = values.cast::<PyList>().unwrap();

            assert!(values.get_item(0).unwrap().is_none());
            for (index, expected) in [(1, true), (2, false)] {
                let value = values.get_item(index).unwrap();
                assert!(value.is_instance_of::<PyBool>());
                assert_eq!(value.extract::<bool>().unwrap(), expected);
            }
            let signed = values.get_item(3).unwrap();
            assert!(signed.is_instance_of::<PyInt>());
            assert_eq!(signed.extract::<i64>().unwrap(), i64::MIN);
            let unsigned = values.get_item(4).unwrap();
            assert!(unsigned.is_instance_of::<PyInt>());
            assert_eq!(unsigned.extract::<u64>().unwrap(), u64::MAX);
            let float = values.get_item(5).unwrap();
            assert!(float.is_instance_of::<PyFloat>());
            assert_eq!(float.extract::<f64>().unwrap(), 1.5);
            let string = values.get_item(6).unwrap();
            assert!(string.is_instance_of::<PyString>());
            assert_eq!(string.extract::<String>().unwrap(), "🚀");
            assert_eq!(
                dict.get_item("empty_list")
                    .unwrap()
                    .unwrap()
                    .cast::<PyList>()
                    .unwrap()
                    .len(),
                0
            );
            assert_eq!(
                dict.get_item("empty_object")
                    .unwrap()
                    .unwrap()
                    .cast::<PyDict>()
                    .unwrap()
                    .len(),
                0
            );
        });
    }

    #[test]
    fn python_entry_points_parse_full_and_header_only_replays() {
        let data = include_bytes!("../test-files/973E29BA437C1AA2B54BC6AFE28BA0B3.replay");
        Python::initialize();
        Python::attach(|py| {
            let module = PyModule::new(py, "_lib").unwrap();
            _lib(&module).unwrap();
            let full = module
                .getattr("parse_replay")
                .unwrap()
                .call1((data.as_slice(),))
                .unwrap();
            let header = module
                .getattr("parse_replay_header_only")
                .unwrap()
                .call1((data.as_slice(),))
                .unwrap();

            assert!(full.is_instance_of::<PyDict>());
            assert!(header.is_instance_of::<PyDict>());
            let frames = full
                .get_item("network_frames")
                .unwrap()
                .get_item("frames")
                .unwrap();
            assert_eq!(frames.len().unwrap(), 10_659);
            assert!(header.get_item("network_frames").unwrap().is_none());
            assert!(full
                .get_item("properties")
                .unwrap()
                .eq(header.get_item("properties").unwrap())
                .unwrap());
        });
    }

    #[test]
    fn invalid_replays_raise_python_exceptions() {
        Python::initialize();
        Python::attach(|py| {
            for result in [parse_replay(py, b""), parse_replay_header_only(py, b"")] {
                let error = result.unwrap_err();
                assert!(error.is_instance_of::<PyException>(py));
                assert!(error.to_string().contains("Boxcars parsing error:"));
            }
        });
    }
}
