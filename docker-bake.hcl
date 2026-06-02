group "default" {
  targets = ["fixture"]
}

target "fixture" {
  dockerfile = "Dockerfile.fixture"
  tags       = ["velnor-actions-fixture:bake"]
  args = {
    PACKAGE = "app-a"
  }
}
