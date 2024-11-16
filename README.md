# BYR Docs CLI

## Install 

Using pip:
```bash
pip3 install byrdocs
```

## Usage

```bash
usage: byrdocs [-h] [--version] [--token TOKEN] [command] [file]

positional arguments:
  command        Command to execute
  file           Path to the file to upload

options:
  -h, --help     show this help message and exit
  --version, -v  show program's version number and exit
  --token TOKEN  Token for login command
```

## Development

Build:

```bash
python3 -m build
```


Push to PyPI:
```bash
python3 -m twine upload --repository pypi dist/* --verbose
```
