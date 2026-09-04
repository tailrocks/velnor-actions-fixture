//! Minimal dependency-free JSON value, parser and canonical writer.
//!
//! The verifier must read evidence back and compare it structurally, so it
//! needs a parser as well as the writer the fixture harness already had. Keys
//! are held in a [`BTreeMap`] so every document this crate emits is canonical
//! and byte-comparable.

use std::collections::BTreeMap;
use std::fmt::Write as _;

/// A parsed JSON value.
#[derive(Debug, Clone, PartialEq)]
pub enum Json {
    /// JSON `null`.
    Null,
    /// JSON `true`/`false`.
    Bool(bool),
    /// JSON number, kept as its source text so round-trips are exact.
    Number(String),
    /// JSON string.
    String(String),
    /// JSON array.
    Array(Vec<Json>),
    /// JSON object with canonically ordered keys.
    Object(BTreeMap<String, Json>),
}

impl Json {
    /// Builds a JSON string value.
    pub fn string(value: impl Into<String>) -> Self {
        Self::String(value.into())
    }

    /// Builds a JSON number from an unsigned integer.
    pub fn number(value: u64) -> Self {
        Self::Number(value.to_string())
    }

    /// Builds a JSON object from key/value pairs.
    pub fn object(entries: impl IntoIterator<Item = (String, Json)>) -> Self {
        Self::Object(entries.into_iter().collect())
    }

    /// Returns the string contents when this value is a string.
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Self::String(value) => Some(value),
            _ => None,
        }
    }

    /// Returns the object entries when this value is an object.
    pub fn as_object(&self) -> Option<&BTreeMap<String, Json>> {
        match self {
            Self::Object(entries) => Some(entries),
            _ => None,
        }
    }

    /// Looks up a direct child of an object value.
    pub fn get(&self, key: &str) -> Option<&Json> {
        self.as_object().and_then(|entries| entries.get(key))
    }

    /// The value's JSON type name, used in diagnostics.
    pub fn type_name(&self) -> &'static str {
        match self {
            Self::Null => "null",
            Self::Bool(_) => "bool",
            Self::Number(_) => "number",
            Self::String(_) => "string",
            Self::Array(_) => "array",
            Self::Object(_) => "object",
        }
    }

    /// Renders canonical JSON: sorted keys, no insignificant whitespace.
    pub fn to_json(&self) -> String {
        let mut output = String::new();
        self.write(&mut output);
        output
    }

    fn write(&self, output: &mut String) {
        match self {
            Self::Null => output.push_str("null"),
            Self::Bool(true) => output.push_str("true"),
            Self::Bool(false) => output.push_str("false"),
            Self::Number(value) => output.push_str(value),
            Self::String(value) => write_string(output, value),
            Self::Array(items) => {
                output.push('[');
                for (index, item) in items.iter().enumerate() {
                    if index != 0 {
                        output.push(',');
                    }
                    item.write(output);
                }
                output.push(']');
            }
            Self::Object(entries) => {
                output.push('{');
                for (index, (key, value)) in entries.iter().enumerate() {
                    if index != 0 {
                        output.push(',');
                    }
                    write_string(output, key);
                    output.push(':');
                    value.write(output);
                }
                output.push('}');
            }
        }
    }
}

fn write_string(output: &mut String, value: &str) {
    output.push('"');
    for character in value.chars() {
        match character {
            '"' => output.push_str("\\\""),
            '\\' => output.push_str("\\\\"),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            character if character.is_control() => {
                let _ = write!(output, "\\u{:04x}", character as u32);
            }
            character => output.push(character),
        }
    }
    output.push('"');
}

/// Parses a complete JSON document, rejecting trailing content.
///
/// # Errors
///
/// Returns a human-readable message for any malformed document.
pub fn parse(input: &str) -> Result<Json, String> {
    let bytes: Vec<char> = input.chars().collect();
    let mut parser = Parser {
        input: &bytes,
        position: 0,
    };
    parser.skip_whitespace();
    let value = parser.value()?;
    parser.skip_whitespace();
    if parser.position != parser.input.len() {
        return Err(format!(
            "trailing content at offset {}: {:?}",
            parser.position, parser.input[parser.position]
        ));
    }
    Ok(value)
}

struct Parser<'a> {
    input: &'a [char],
    position: usize,
}

impl Parser<'_> {
    fn peek(&self) -> Option<char> {
        self.input.get(self.position).copied()
    }

    fn skip_whitespace(&mut self) {
        while matches!(self.peek(), Some(' ' | '\t' | '\n' | '\r')) {
            self.position += 1;
        }
    }

    fn expect(&mut self, expected: char) -> Result<(), String> {
        match self.peek() {
            Some(found) if found == expected => {
                self.position += 1;
                Ok(())
            }
            Some(found) => Err(format!(
                "expected {expected:?} at offset {}, found {found:?}",
                self.position
            )),
            None => Err(format!("expected {expected:?}, found end of input")),
        }
    }

    fn literal(&mut self, text: &str) -> Result<(), String> {
        for character in text.chars() {
            self.expect(character)?;
        }
        Ok(())
    }

    fn value(&mut self) -> Result<Json, String> {
        match self.peek() {
            Some('n') => {
                self.literal("null")?;
                Ok(Json::Null)
            }
            Some('t') => {
                self.literal("true")?;
                Ok(Json::Bool(true))
            }
            Some('f') => {
                self.literal("false")?;
                Ok(Json::Bool(false))
            }
            Some('"') => Ok(Json::String(self.string()?)),
            Some('[') => self.array(),
            Some('{') => self.object(),
            Some(character) if character == '-' || character.is_ascii_digit() => self.number(),
            Some(character) => Err(format!(
                "unexpected character {character:?} at offset {}",
                self.position
            )),
            None => Err("unexpected end of input".to_owned()),
        }
    }

    fn array(&mut self) -> Result<Json, String> {
        self.expect('[')?;
        let mut items = Vec::new();
        self.skip_whitespace();
        if self.peek() == Some(']') {
            self.position += 1;
            return Ok(Json::Array(items));
        }
        loop {
            self.skip_whitespace();
            items.push(self.value()?);
            self.skip_whitespace();
            match self.peek() {
                Some(',') => self.position += 1,
                Some(']') => {
                    self.position += 1;
                    return Ok(Json::Array(items));
                }
                other => {
                    return Err(format!(
                        "expected ',' or ']' at offset {}, found {other:?}",
                        self.position
                    ))
                }
            }
        }
    }

    fn object(&mut self) -> Result<Json, String> {
        self.expect('{')?;
        let mut entries = BTreeMap::new();
        self.skip_whitespace();
        if self.peek() == Some('}') {
            self.position += 1;
            return Ok(Json::Object(entries));
        }
        loop {
            self.skip_whitespace();
            let key = self.string()?;
            self.skip_whitespace();
            self.expect(':')?;
            self.skip_whitespace();
            let value = self.value()?;
            if entries.insert(key.clone(), value).is_some() {
                return Err(format!("duplicate object key {key:?}"));
            }
            self.skip_whitespace();
            match self.peek() {
                Some(',') => self.position += 1,
                Some('}') => {
                    self.position += 1;
                    return Ok(Json::Object(entries));
                }
                other => {
                    return Err(format!(
                        "expected ',' or '}}' at offset {}, found {other:?}",
                        self.position
                    ))
                }
            }
        }
    }

    fn number(&mut self) -> Result<Json, String> {
        let start = self.position;
        if self.peek() == Some('-') {
            self.position += 1;
        }
        while matches!(self.peek(), Some('0'..='9' | '.' | 'e' | 'E' | '+' | '-')) {
            self.position += 1;
        }
        let text: String = self.input[start..self.position].iter().collect();
        if text.is_empty() || text == "-" {
            return Err(format!("invalid number at offset {start}"));
        }
        Ok(Json::Number(text))
    }

    fn string(&mut self) -> Result<String, String> {
        self.expect('"')?;
        let mut value = String::new();
        loop {
            let character = self
                .peek()
                .ok_or_else(|| "unterminated string".to_owned())?;
            self.position += 1;
            match character {
                '"' => return Ok(value),
                '\\' => {
                    let escape = self
                        .peek()
                        .ok_or_else(|| "unterminated escape".to_owned())?;
                    self.position += 1;
                    match escape {
                        '"' => value.push('"'),
                        '\\' => value.push('\\'),
                        '/' => value.push('/'),
                        'b' => value.push('\u{8}'),
                        'f' => value.push('\u{c}'),
                        'n' => value.push('\n'),
                        'r' => value.push('\r'),
                        't' => value.push('\t'),
                        'u' => {
                            let mut code = 0u32;
                            for _ in 0..4 {
                                let digit = self
                                    .peek()
                                    .and_then(|item| item.to_digit(16))
                                    .ok_or_else(|| "invalid \\u escape".to_owned())?;
                                self.position += 1;
                                code = code * 16 + digit;
                            }
                            value.push(char::from_u32(code).unwrap_or('\u{fffd}'));
                        }
                        other => return Err(format!("invalid escape {other:?}")),
                    }
                }
                other => value.push(other),
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{parse, Json};

    #[test]
    fn round_trips_nested_documents() {
        let text = r#"{"b":[1,2,{"c":null}],"a":"x\ny"}"#;
        let value = parse(text).expect("valid document");
        assert_eq!(value.to_json(), r#"{"a":"x\ny","b":[1,2,{"c":null}]}"#);
    }

    #[test]
    fn rejects_trailing_content_and_duplicate_keys() {
        assert!(parse("{} {}").is_err());
        assert!(parse(r#"{"a":1,"a":2}"#).is_err());
    }

    #[test]
    fn object_helper_sorts_keys() {
        let value = Json::object([
            ("z".to_owned(), Json::number(1)),
            ("a".to_owned(), Json::Bool(true)),
        ]);
        assert_eq!(value.to_json(), r#"{"a":true,"z":1}"#);
    }
}
