"""
File handling utilities for thinFTP

This module defines the `FileHandler` class used by the thinFTP server to 
manage filesystem operations securely within a defined root directory. It 
ensures safe access to files and directories and provides support for FTP-style 
commands such as directory navigation, file listing, reading/writing files, 
deletion, and renaming.

Classes:
    FileHandler: Encapsulates all file operations, enforcing confinement to 
    the FTP server's root directory. Raises appropriate exceptions for invalid 
    actions.

Exceptions:
    FileHandlerError: Raised for invalid file-related operations such as 
    attempting to get the size of or delete a non-file.

Dependencies:
    - pathlib.Path: For file path resolution and operations.
    - stat: For interpreting file permission modes.
    - time: For formatting file modification times.
    - .errors.FileHandlerError: Custom exception used in this module.
"""

import stat
import time
from pathlib import Path
from .errors import FileHandlerError

class FileHandler:
    """
    Custom File Handler class for thinFTP.

    Handles file operations such as navigating directories, listing contents,
    reading and writing files, and renaming or deleting files and directories.
    """

    def __init__(self, root_dir):
        """
        Initialize the FileHandler with a root directory.

        Parameters:
            root_dir (str): The root directory for file operations.
        """
        self.root_dir = Path(root_dir).resolve()
        self.cur_dir = self.root_dir
        self.ren_old = None

    def resolve_path(self, path):
        """
        Resolve a given path to an absolute path within the root directory.

        Parameters:
            path (str): The path to resolve.

        Returns:
            Path: An absolute Path object.
        """
        if path.startswith('/') or path.startswith('\\'):
            return (self.root_dir / path.lstrip('/\\')).resolve()
        return (self.cur_dir / path).resolve()

    def pwd(self):
        """
        Get the current working directory relative to the root directory.

        Returns:
            str: The current directory as a string.
        """
        if self.cur_dir == self.root_dir:
            return '/'
        return '/' + self.cur_dir.relative_to(self.root_dir).as_posix()

    def get_abs(self, path):
        """
        Get the absolute path of a given path relative to the root directory.

        Parameters:
            path (str): The path to resolve.

        Returns:
            str: The absolute path as a string.
        """
        new_dir = self.resolve_path(path)
        return '/' + new_dir.relative_to(self.root_dir).as_posix()

    def cwd(self, path):
        """
        Change the current working directory.

        Parameters:
            path (str): The directory to change to.

        Raises:
            FileNotFoundError: If the directory does not exist.
            NotADirectoryError: If the path is not a directory.
            PermissionError: If attempting to move outside the root directory.
        """
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
        """
        Change to the parent directory.

        Raises:
            FileNotFoundError: If the parent directory does not exist.
            PermissionError: If attempting to move outside the root directory.
        """
        par_dir = self.cur_dir.parent.resolve()
        if par_dir.exists():
            if not par_dir.absolute().is_relative_to(self.root_dir):
                raise PermissionError('Attempt to move behind root directory')
            self.cur_dir = par_dir
        else:
            raise FileNotFoundError

    def mkdir(self, path):
        """
        Create a new directory.

        Parameters:
            path (str): Path of directory to create.
        """
        self.resolve_path(path).mkdir(parents=True)

    def name_ls(self, path):
        """
        List the names of entries in a directory.

        Parameters:
            path (str): The directory to list.

        Returns:
            list: A list of Path objects representing entries in the directory.
        
        Raises:
            PermissionError: If attempting to move outside the root directory.
        """
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
        """
        List the contents of the specified directory.

        Parameters:
            path (str): The directory to list.

        Returns:
            list: A list of strings representing the contents of the directory, in
            the format:

            `<permissions> <nlinks> <owner> <group> <size> <modtime> <name>`

            If the directory does not exist, an empty list is returned.
        """
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
        """
        Read a file in chunks.

        Parameters:
            fname (str): The file to read.
            type (str): The transfer type ('A' for ASCII, 'I' for binary).

        Yields:
            bytes: Chunks of the file content.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If attempting to move outside the root directory.
        """
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
        """
        Get the size of a file.

        Parameters:
            fname (str): The file to check.

        Returns:
            int: The size of the file in bytes.

        Raises:
            PermissionError: If attempting to move outside the root directory.
            FileHandlerError: If the path is not a file.
        """
        path = self.resolve_path(fname)
        if not path.is_relative_to(self.root_dir):
            raise PermissionError('Attempt to move behind root directory')
        if not path.is_file():
            raise FileHandlerError(f'Not a file: {fname!r}')
        return path.stat().st_size

    def delete(self, fname):
        """
        Delete a file.

        Parameters:
            fname (str): The file to delete.

        Raises:
            PermissionError: If attempting to move outside the root directory.
            FileHandlerError: If the path is not a file.
        """
        path = self.resolve_path(fname)
        if not path.is_relative_to(self.root_dir):
            raise PermissionError('Attempt to move behind root directory')
        if not path.is_file():
            raise FileHandlerError(f'Not a file: {fname!r}')
        path.unlink()

    def rmdir(self, path):
        """
        Remove a directory.

        Parameters:
            path (str): The directory to remove.

        Raises:
            FileNotFoundError: If the directory does not exist.
            NotADirectoryError: If the path is not a directory.
            PermissionError: If attempting to move outside the root directory.
        """
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
        """
        Mark a file or directory for renaming.

        Parameters:
            old (str): Existing file/directory name.

        Raises:
            FileNotFoundError: If the original path does not exist.
            PermissionError: If attempting to move outside the root directory.
        """
        self.ren_old = self.resolve_path(old)
        if not self.ren_old.is_relative_to(self.root_dir):
            self.ren_old = None
            raise PermissionError('Attempt to move behind root directory')
        if not self.ren_old.exists():
            self.ren_old = None
            raise FileNotFoundError
            
    def rename_to(self, new):
        """
        Rename a previously marked file or directory.

        Parameters:
            new (str): New file/directory name.
        """
        new = self.resolve_path(new)
        self.ren_old.rename(new)
        self.ren_old = None
    
    def write(self, fname, data):
        """
        Write data to a file.

        Parameters:
            fname (str): The file to write to.
            data (iterable): An iterable of bytes to write.

        Raises:
            PermissionError: If attempting to move outside the root directory.
        """
        path = self.resolve_path(fname)
        if not path.is_relative_to(self.root_dir):
            raise PermissionError('Attempt to move behind root directory')
        with open(path, 'wb') as f:
            for chunk in data:
                f.write(chunk)
                    
