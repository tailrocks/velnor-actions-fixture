fn main() {
    println!("{}", shared::label("app-a"));
}

#[cfg(test)]
mod tests {
    #[test]
    fn prints_expected_label() {
        assert_eq!(shared::label("app-a"), "fixture::app-a");
    }
}
