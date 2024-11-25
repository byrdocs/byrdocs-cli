from pathlib import Path

history_path = Path.home() / ".config" / "byrdocs" / "history"

class UploadHistory:
    def __init__(self):
        self.history: list[list[str]] = []  # [file, md5, timestamp]
        if history_path.exists():
            self._read()
        else:
            history_path.touch()
            self.history = []
    
    def _read(self) -> None:
        with history_path.open("r") as f:
            try:
                self.history = [line.split(":") for line in f.read().splitlines()]
            except:
                raise ValueError("无法读取历史记录文件，可能已经损坏")
    
    def _write(self):
        with history_path.open("w") as f:
            for line in self.history:
                f.write(":".join(line) + "\n")
    
    def _with_update(func):
        def wrapper(self, *args, **kwargs):
            self._read()
            result = func(self, *args, **kwargs)
            self._write()
            return result
        return wrapper

    @_with_update
    def add(self, file, md5, timestamp):
        self.history.append([file, md5, str(timestamp)])
        
    @_with_update  
    def get(self) -> list[list[str]]:
        return self.history
    
    @_with_update
    def clear(self):
        self.history = []
    
    @_with_update
    def remove(self, index):
        self.history.pop(index)
        
class Tests:
    def __init__(self):
        self.history = UploadHistory()
        self.history.clear()
    
    def test_add(self):
        self.history.add("test1", "md5", "time")
        print(self.history.get())
        assert self.history.get() == [["test1", "md5", "time"]]
        
    def test_remove(self):
        self.history.add("test2", "md5", "time")
        self.history.remove(0)
        # print(self.history.get())
        assert self.history.get() == [["test2", "md5", "time"]]
        
    # def test_clear(self):
    #     self.history.add("test1", "md5", "time")
    #     self.history.add("test2", "md5", "time")
    #     self.history.clear()
    #     assert self.history.get() == []
        
    def test_get(self):
        self.history.add("test1", "md5", "time")
        self.history.add("test2", "md5", "time")
        assert self.history.get() == [["test1", "md5", "time"], ["test2", "md5", "time"]]
        
    def run(self):
        self.test_add()
        self.test_remove()
        self.test_clear()
        self.test_get()
        print("All tests passed.")
        
# Tests().run()