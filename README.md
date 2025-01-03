# BYR Docs CLI

## 安装

### 使用 `pip` 安装：
```bash
pip3 install byrdocs-cli
```

### 使用 `pipx` 安装（当 `pip` 无法使用时）：

根据包管理器选择对应的命令安装 `pipx`：
```bash
pip install pipx
sudo apt install pipx
sudo dnf install pipx
sudo pacman -S pipx
```

再使用 `pipx` 进行安装：
```
pipx install byrdocs-cli   
```

### 使用 `homebrew` 安装（MacOS 或 Linux）：
```zsh
brew tap byrdocs/homebrew-byrdocs-cli
brew install byrdocs-cli
```

### 更新

使用 `pip`:
```bash
pip install byrdocs-cli --upgrade 
```

使用 `pipx`:
```bash
pipx upgrade byrdocs-cli
```

使用 `homebrew`:
```zsh
brew upgrade byrdocs-cli
```

## 使用

```
用法: byrdocs [-h] [--token TOKEN] [command] [file]

命令：
  upload <文件路径>    上传文件 [默认命令]
  login               登录到 BYR Docs
  logout              退出登录
  init                交互式生成文件元信息文件
  validate            (待实现) 验证元信息文件的合法性

参数:
  command        要执行的命令
  file           要上传的文件路径

选项:
  -h, --help     输出该帮助信息并退出
  --token TOKEN  指定登录时使用的 token

示例：
  $ byrdocs login
  $ byrdocs /home/exam_paper.pdf
  $ byrdocs logout
  $ byrdocs init
```

## 开发

构建:

```bash
python3 -m build
```


发布到 PyPI:
```bash
python3 -m twine upload --repository pypi dist/* --verbose
```

测试:
```bash
python test.py [arguments]
```
