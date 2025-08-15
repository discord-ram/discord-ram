![Light Logo](.github/assets/discord-ram-readme-logo-light.png#gh-light-mode-only)
![Dark Logo](.github/assets/discord-ram-readme-logo-dark.png#gh-dark-mode-only)

An asynchronous, modular, and high-performance framework
for building Discord bots with Python 3.

The project follows the principles of modularity and efficient use of the programming language to achieve the full performance capabilities of Python 3.
The main architectural principle is the separation of the abstraction-driven, functional framework from the underlying structures and bare implementations.
This approach lets developers either tap into the magic of automated abstractions to speed up their workflow, or work with bare implementations to bring their own ideas to life.

# Compatibility

- Python 3.10 and above (Python 3.13 is not yet supported).

- Discord API v6 and above (v10 recommended).

# Installation

> [!WARNING]
> The framework is in an alpha stage and cannot yet be installed via standard package managers. Manual installation is possible, but it may be unstable. If you decide to try it, we welcome all issues and pull requests.

```sh
$ pip install discord-ram  # `ramx` will be installed

$ pip install discord-ram[full]  # `ramx` and `ram`
```

## Manual

```sh
$ pip install git+https://github.com/discord-ram/discord-ram
```

## Performance advices

- Use [uvloop](https://pypi.org/uvloop) (for Windows [winloop](https://pypi.org/project/winloop/)): drop-in replacement for the default asyncio event loop for lower latency and higher throughput.
- Run your project with `-OO` optimization flag ([PEP 488](https://peps.python.org/pep-0488/)): this removes assertions and docstrings in runtime, which slightly reduces memory usage and improves performance.

# Inspiration

| Repository                                              | Description                                                            |
| ------------------------------------------------------- | ---------------------------------------------------------------------- |
| [hikari-py/hikari](https://github.com/hikari-py/hikari) | A Discord API wrapper for Python and asyncio built on good intentions. |
