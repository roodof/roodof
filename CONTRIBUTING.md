# Contributing

Thanks for helping with Roodof.

- **Bugs and ideas:** open an issue. Say which Roodof version and operating system you use, and what you expected to see.
- **Security problems:** follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
- **Pull requests:** keep them small and focused. Run the tests before sending:

  ```
  python -m pytest
  ```

  [tests/test_trust.py](tests/test_trust.py) guards Roodof's core promise: logs are read locally, no log text reaches the page or the cache, and no agent data is sent anywhere. Changes must keep those tests passing.
- **Privacy:** never paste real agent logs, prompts or tokens into issues or test fixtures. Use invented sample data.

By contributing, you agree that your contribution is licensed under the [MIT license](LICENSE).
