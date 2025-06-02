# Custom File Handler class for thinFTP
import stat
import time
from pathlib import Path
from .errors import FileHandlerError

class FileHandler:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir).resolve()
        self.cur_dir = self.root_dir
        self.ren_old = None

    def resolve_path(self, path):
        if path.startswith('/') or path.startswith('\\'):
            return (self.root_dir / path.lstrip('/\\')).resolve()
        return (self.cur_dir / path).resolve()

    def pwd(self):
        if self.cur_dir == self.root_dir:
            return '/'
        return '/' + self.cur_dir.relative_to(self.root_dir).as_posix()

    def get_abs(self, path):
        new_dir = self.resolve_path(path)
        return '/' + new_dir.relative_to(self.root_dir).as_posix()

    def cwd(self, path):
        new_path = self.resolve_path(path)
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
            if not par_dir.absolute().is_relative_to(self.root_dir):
                raise PermissionError('Attempt to move behind root directory')
            self.cur_dir = par_dir
        else:
            raise FileNotFoundError

    def mkdir(self, path):
        self.resolve_path(path).mkdir(parents=True)

    def name_ls(self, path):
        target_dir = self.resolve_path(path)

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
        
        return matches
    
    def ls(self, path):
        matches = self.name_ls(path)
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

    def read(self, fname, type):
        mode = 'rb' if type == 'I' else 'r'
        path = self.resolve_path(fname)
        with open(path, mode) as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                if mode == 'r':
                    yield chunk.replace('\n', '\r\n').encode('ascii')
                else:
                    yield chunk

    def size(self, fname):
        path = self.resolve_path(fname)
        if not path.is_relative_to(self.root_dir):
            raise PermissionError('Attempt to move behind root directory')
        if not path.is_file():
            raise FileHandlerError(f'Not a file: {fname!r}')
        return path.stat().st_size

    def delete(self, fname):
        path = self.resolve_path(fname)
        if not path.is_relative_to(self.root_dir):
            raise PermissionError('Attempt to move behind root directory')
        if not path.is_file():
            raise FileHandlerError(f'Not a file: {fname!r}')
        path.unlink()             

    def rmdir(self, path):
        path = self.resolve_path(path)
        if path.exists():
            if path.is_dir():
                if not path.is_relative_to(self.root_dir):
                    raise PermissionError('Attempt to move behind root directory')
                path.rmdir()
                return
            raise NotADirectoryError
        raise FileNotFoundError

    def rename_from(self, old):
        self.ren_old = self.resolve_path(old)
        if not self.ren_old.is_relative_to(self.root_dir):
            self.ren_old = None
            raise PermissionError('Attempt to move behind root directory')
        if not self.ren_old.exists():
            self.ren_old = None
            raise FileNotFoundError
            
    def rename_to(self, new):
        new = self.resolve_path(new)
        self.ren_old.rename(new)
        self.ren_old = None
    
    def write(self, fname, data):
        path = self.resolve_path(fname)
        if not path.is_relative_to(self.root_dir):
            raise PermissionError('Attempt to move behind root directory')
        with open(path, 'wb') as f:
            for chunk in data:
                f.write(chunk)
                    
