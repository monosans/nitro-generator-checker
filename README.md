# nitro-generator-checker

[![CI](https://github.com/monosans/nitro-generator-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/monosans/nitro-generator-checker/actions/workflows/ci.yml)

![Screenshot](screenshot.png)

Discord Nitro codes generator and checker with built-in proxy grabber. Saves working ones to a file or Webhook.

## Installation and usage

### Standalone executable

This is the easiest way, but it is only available for x86-64 Windows, x86-64/arm64 macOS and x86-64 Linux. Just download the archive for your OS from [nightly.link](https://nightly.link/monosans/nitro-generator-checker/workflows/ci/main?preview), unzip it, edit `config.toml` and run the `nitro_generator_checker` executable.

If Windows antivirus detects the executable file as a virus, please read [this](https://github.com/Nuitka/Nuitka/issues/2496#issuecomment-1762836583).

### Docker

- [Install `Docker Compose`](https://docs.docker.com/compose/install/).
- Download and unpack [the archive with the program](https://github.com/monosans/nitro-generator-checker/archive/refs/heads/main.zip).
- Edit `config.toml` to your preference.
- Run the following commands:
  ```bash
  docker compose build --pull
  docker compose up --no-log-prefix
  ```

### Running from source code

#### Desktop

- Install [Python](https://python.org/downloads). The minimum version required is 3.8.
- Download and unpack [the archive with the program](https://github.com/monosans/nitro-generator-checker/archive/refs/heads/main.zip).
- Edit `config.toml` to your preference.
- Run the script that installs dependencies and starts `nitro-generator-checker`:
  - On Windows run `start.cmd`
  - On Unix-like operating systems run `start.sh`

#### Termux

To use `nitro-generator-checker` in Termux, knowledge of the Unix command-line interface is required.

- Download Termux from [F-Droid](https://f-droid.org/en/packages/com.termux/). [Don't download it from Google Play](https://github.com/termux/termux-app#google-play-store-experimental-branch).
- Run the following command (it will automatically update Termux packages, install Python, and download and install `nitro-generator-checker`):
  ```bash
  bash <(curl -fsSL 'https://raw.githubusercontent.com/monosans/nitro-generator-checker/main/install-termux.sh')
  ```
- Edit `~/nitro-generator-checker/config.toml` to your preference using a text editor (vim/nano).
- To run `nitro-generator-checker` use the following command:
  ```bash
  cd ~/nitro-generator-checker && sh start-termux.sh
  ```

## License

[MIT](LICENSE)
