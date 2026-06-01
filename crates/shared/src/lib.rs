pub fn label(name: &str) -> String {
    format!("fixture::{name}")
}

#[cfg(test)]
mod tests {
    use super::label;

    #[test]
    fn labels_values() {
        assert_eq!(label("app-a"), "fixture::app-a");
    }
}
