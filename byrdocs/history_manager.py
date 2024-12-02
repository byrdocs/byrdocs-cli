import json
from pathlib import Path

history_path = Path.home() / ".config" / "byrdocs" / "history.json"

'''
File format:
{
    "history": [
        {
            "file": "file_path",
            "md5": "md5",
            "timestamp": "timestamp"
        }
    ]
}
'''

class UploadHistory:
    def __init__(self):
        self.data: dict[str, list[dict[str, str]]] = {}
        self.history: list[dict[str, str]] = []
        try:
            if history_path.exists():
                self._read()
            else:
                history_path.touch()
                self.history = []
                self.data = {"history": self.history}
        except json.JSONDecodeError:
            self.history = []
            self.data = {"history": self.history}
            self._write()
    
    def _read(self) -> None:
        with history_path.open("r") as f:
            self.data = json.load(f)
            self.history = self.data.get("history", [])
    
    def _write(self):
        self.data["history"] = self.history
        with history_path.open("w") as f:
            json.dump(self.data, f, indent=4)
    
    def _with_update(func):
        def wrapper(self, *args, **kwargs):
            self._read()
            result = func(self, *args, **kwargs)
            self.data["history"] = self.history
            self._write()
            return result
        return wrapper

    @_with_update
    def add(self, file: str, md5: str, timestamp: str):
        self.history.append({
            "file": file,
            "md5": md5,
            "timestamp": timestamp
        })
        
    @_with_update  
    def get(self) -> list[dict[str, str]]:
        return self.history
    
    @_with_update
    def clear(self):
        self.history = []
    
    @_with_update
    def remove(self, index):
        self.history.pop(index)
        
class Tests:
    def test_add(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        assert history.get() == [{"file": "file", "md5": "md5", "timestamp": "timestamp"}]
    
    def add(self):
        history = UploadHistory()
        history.add("file1", "ab345678901234567890123456789012.pdf", "1733110485.531392")
        history.add("file2", "cd345678901234567890123456789012.zip", "1733010485.531392")
        history.add("file3", "ef345678901234567890123456789012.pdf", "1733050485.531392")
        history.add("测试 空 格 文 件 名 .zip", "bbbb5678901234567890123456789012.pdf", "1730050485.531392")
    
    def test_remove(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        history.remove(0)
        assert history.get() == []
    
    def test_clear(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        history.clear()
        assert history.get() == []
    
    def test_get(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        assert history.get() == [{"file": "file", "md5": "md5", "timestamp": "timestamp"}]
    
    def test_multiple_add(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        history.add("file2", "md52", "timestamp2")
        assert history.get() == [
            {"file": "file", "md5": "md5", "timestamp": "timestamp"},
            {"file": "file2", "md5": "md52", "timestamp": "timestamp2"}
        ]
    
    def test_multiple_remove(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        history.add("file2", "md52", "timestamp2")
        history.remove(0)
        assert history.get() == [
            {"file": "file2", "md5": "md52", "timestamp": "timestamp2"}
        ]
    
    def test_multiple_clear(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        history.add("file2", "md52", "timestamp2")
        history.clear()
        assert history.get() == []
    
    def test_multiple_get(self):
        history = UploadHistory()
        history.add("file", "md5", "timestamp")
        history.add("file2", "md52", "timestamp2")
        assert history.get() == [
            {"file": "file", "md5": "md5", "timestamp": "timestamp"},
            {"file": "file2", "md5": "md52", "timestamp": "timestamp2"}
        ]
    

if __name__ == "__main__":
    tests = Tests()
    tests.add()
    # tests.test_clear()
    # tests.test_add()
    # tests.test_remove()
    # tests.test_multiple_add()
    # tests.test_multiple_remove()
    # tests.test_multiple_get()
    # tests.test_multiple_clear()
    # tests.test_multiple_add()