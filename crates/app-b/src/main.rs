fn main() {
    println!("{}", shared::label("app-b"));
}

#[cfg(test)]
mod tests {
    #[test]
    fn prints_expected_label() {
        assert_eq!(shared::label("app-b"), "fixture::app-b");
    }
}
