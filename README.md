# BYR Docs CLI

## Install 

### Using pip:
```bash
pip3 install byrdocs-cli
```

### Using pipx (alternated, when you have problem with pip):

Choose one of the following commands according to your package manager:
```bash
sudo apt install pipx
sudo dnf install pipx
sudo pacman -S pipx
```

Then:
```
pipx install byrdocs-cli    
```

## Usage

```
usage: byrdocs [-h] [--token TOKEN] [command] [file]

Commands:
  upload <file>    Upload a file. If no command is specified, it defaults to upload.
  login            Authenticate with BYR Docs and obtain a token.
  logout           Remove the locally stored authentication token.

positional arguments:
  command        Command to execute
  file           Path to the file to upload

options:
  -h, --help     show this help message and exit
  --token TOKEN  Token for login command

Examples:
 $ byrdocs login
 $ byrdocs /home/exam_paper.pdf
 $ byrdocs logout
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

Test:
```bash
python test.py [arguments]
```
