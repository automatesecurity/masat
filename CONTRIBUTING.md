# Contributing to MASAT

Thank you for your interest in contributing to MASAT – the Modular Attack Surface Analysis Tool. Your contributions help make MASAT better and more secure for everyone.

## How to Contribute

There are several ways to contribute to MASAT:

- **Reporting Bugs:**  
  Please use the [GitHub Issues](https://github.com/automatesecurity/masat/issues) to report any bugs or security issues you discover.

- **Feature Requests:**  
  If you have ideas for new features or enhancements, please open an issue to discuss them before starting work.

- **Pull Requests:**  
  1. Fork the repository.
  2. Create a new branch for your feature or bug fix:
     ```bash
     git checkout -b feature/your-feature-name
     ```
  3. Commit your changes with clear commit messages.
  4. Ensure that all new code adheres to our coding standards and style guidelines.
  5. Write tests for any new vulnerability checks, scanner modules, or other functionality.
  6. Run the test suite locally using:
     ```bash
     pytest
     ```
  7. Push your branch and open a pull request against the main branch.

## Testing & Code Coverage

- **Tests:**  
  MASAT includes unit tests for each scanner module and vulnerability check using **pytest** and **pytest-asyncio**.  
  Any new vulnerability checks or scanner modules must have accompanying tests that are created and passing before merging.

- **Code Coverage:**  
  We use **pytest-cov** to monitor code coverage. Please ensure that your contributions maintain or improve the current coverage levels:
  ```bash
  pytest --cov=masat --cov-report=term-missing
  ```

## License Requirements
MASAT is licensed under the Apache License 2.0. Contributions to MASAT are subject to this license, which means:

Attribution: All modifications and derivative works must include appropriate attribution to the original source code.
License Notice: Any files you add must include a header referencing the Apache 2.0 license.
Patent Grant: Contributors grant a license for any patents that might be infringed by their contributions.
Please include the following header in any new files you add:

```python
#!/usr/bin/env python3
"""
Author: [Your Name]
Date: [YYYY-MM-DD]
Description: [Brief description of the file/module]
License: Apache License 2.0 – http://www.apache.org/licenses/LICENSE-2.0
"""
```

## Development Workflow
Fork the repository on GitHub and clone your fork locally.
Create a branch for your feature or fix:
```bash
git checkout -b feature/your-feature-name
```

Develop your changes and write tests for any new functionality. Run the tests with:
```bash
pytest
```

Commit your changes with clear messages and push your branch:
```bash
git push origin feature/your-feature-name
```

Open a pull request against the main branch. Please include details on your changes and any related issues.

## Questions?
If you have any questions or need further guidance, please open an issue or contact the maintainers.

Thank you for helping improve MASAT!