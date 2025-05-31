# Custom File Handler class for thinFTP
import stat
import time
from pathlib import Path
from .errors import FileHandlerError

class FileHandler:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir).resolve()
        self.cur_dir = self.root_dir

    def pwd(self):
        if self.cur_dir == self.root_dir:
            return '/'
        return '/' + self.cur_dir.relative_to(self.root_dir).as_posix()

    def get_abs(self, path):
        new_dir = (self.cur_dir / path).resolve()
        return '/' + new_dir.relative_to(self.root_dir).as_posix()

    def cwd(self, path):
        new_path = (self.cur_dir / path).resolve()
        if new_path.exists():
            if new_path.is_dir():
                if not new_path.is_relative_to(self.root_dir):
                    raise PermissionError('Attempt to move behind root directory')
                self.cur_dir = new_path
            else:
                raise NotADirectoryError
        else:
            raise FileNotFoundError

    def cd_up(self):
        par_dir = self.cur_dir.parent.resolve()
        if par_dir.exists():
            if not par_dir.is_relative_to(self.root_dir):
                raise PermissionError('Attempt to move behind root directory')
            self.cur_dir = par_dir
        else:
            raise FileNotFoundError

    def mkdir(self, path):
        (self.cur_dir / path).mkdir(parents=True)
    
    def ls(self, path):
        target_dir = (self.cur_dir / path).resolve()

        if target_dir.exists():
            if not target_dir.is_relative_to(self.root_dir):
                raise PermissionError('Attempt to move behind root directory')
            matches = target_dir.iterdir() if target_dir.is_dir() else [target_dir]
        else:
            matches = target_dir.glob(path)
        
        matches = list(matches)
        for i in range(len(matches)):
            try:
                entry = matches[i].resolve()
                if not entry.is_relative_to(self.root_dir):
                    matches.pop(i)
            except FileNotFoundError:
                continue
        
        if not matches:
            return []
        
        lines = []
        for entry in sorted(matches):
            stats = entry.stat()
            perms = stat.filemode(stats.st_mode)
            size = stats.st_size
            mtime = time.strftime("%b %d %H:%M", time.localtime(stats.st_mtime))
            lines.append(f"{perms} 1 user group {size:>8} {mtime} {entry.name}")
        
        return lines
             
