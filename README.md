# nitro-generator-checker

[![CI](https://github.com/monosans/nitro-generator-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/monosans/nitro-generator-checker/actions/workflows/ci.yml)

![Screenshot](screenshot.png)

Discord Nitro codes generator and checker with built-in proxy grabber. Saves working ones to a file or Webhook.

## Installation and usage

- Download and unpack [the archive with the program](https://github.com/monosans/nitro-generator-checker/archive/refs/heads/main.zip).
- Edit `config.ini` according to your preference.
- Install [Python](https://python.org/downloads) (minimum required version is 3.7).
- Install dependencies and run the script. There are 2 ways to do this:

  - Automatic:
    - On Windows run `start.cmd`
    - On Unix-like OS run `start.sh`
  - Manual:
    <details>
      <summary>Windows (click to expand)</summary>

    1. `cd` into the unpacked folder

    1. Install dependencies with the command:

       ```bash
       py -m pip install -U --no-cache-dir --disable-pip-version-check pip setuptools wheel; py -m pip install -U --no-cache-dir --disable-pip-version-check -r requirements.txt
       ```

    1. Run with the command:

       ```bash
       py -m nitro_generator_checker
       ```

    </details>
    <details>
      <summary>Unix-like OS (click to expand)</summary>

    1. `cd` into the unpacked folder

    1. Install dependencies with the command:

       ```bash
       python3 -m pip install -U --no-cache-dir --disable-pip-version-check pip setuptools wheel && python3 -m pip install -U --no-cache-dir --disable-pip-version-check -r requirements.txt
       ```

    1. Run with the command:

       ```bash
       python3 -m nitro_generator_checker
       ```

    </details>

## License

[MIT](LICENSE)
