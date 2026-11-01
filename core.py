"""Download signed upstream packages and invoke the original Windows CLI."""
from __future__ import annotations
import concurrent.futures
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("REBOOTERX_DATA_DIR", os.environ.get("OPTIMIZERNXT_DATA_DIR", str(BASE / "data"))))
STUDIO_URL = "https://github.com/hiamtrung103/RebooterX-Studio"
REPO = "hellzerg/optimizerNXT"
PROJECT_URL = f"https://github.com/{REPO}"
API = f"https://api.github.com/repos/{REPO}"


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".download-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git_hash(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


class Repository:
    def __init__(self, data: Path = DATA):
        self.data = data

    def request(self, url: str, limit: int = 32 * 1024 * 1024) -> bytes:
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "RebooterX-Studio/2.0",
                    "Accept": "application/vnd.github+json" if url.startswith(API) else "*/*",
                })
                with urllib.request.urlopen(request, timeout=25) as response:
                    content = response.read(limit + 1)
                if len(content) > limit:
                    raise ValueError("Download exceeds size limit.")
                return content
            except urllib.error.HTTPError as error:
                if error.code < 500 and error.code != 429:
                    if error.code in (403, 429):
                        raise RuntimeError("GitHub API limit/access denied. Try again later.") from error
                    raise
                if attempt == 2:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
            time.sleep(attempt + 1)
        raise RuntimeError("Download failed.")

    @staticmethod
    def packages_from_tree(tree: dict) -> list[dict]:
        if tree.get("truncated") or not re.fullmatch(r"[0-9a-f]{40}", tree.get("sha", "")):
            raise ValueError("Invalid or incomplete GitHub tree.")
        blobs = {item["path"]: item for item in tree["tree"]
                 if item.get("type") == "blob" and item.get("mode") == "100644"}
        result = []
        for path, item in sorted(blobs.items()):
            parts = PurePosixPath(path).parts
            if len(parts) != 2 or parts[0] != "yaml" or PurePosixPath(path).suffix not in (".yaml", ".yml"):
                continue
            if not re.fullmatch(r"[A-Za-z0-9_-]+\.ya?ml", parts[1]):
                continue
            if path + ".sig" not in blobs:
                continue
            sig = blobs[path + ".sig"]
            if not all(re.fullmatch(r"[0-9a-f]{40}", x.get("sha", "")) for x in (item, sig)):
                raise ValueError("Invalid blob checksum.")
            result.append({"path": path, "name": parts[1], "sha": item["sha"],
                           "sig_sha": sig["sha"], "revision": tree["sha"]})
        if not result:
            raise ValueError("No signed YAML packages found in the official repository.")
        return result

    def catalog(self) -> tuple[list[dict], str]:
        cache = self.data / "catalog.json"
        try:
            raw = self.request(API + "/git/trees/main?recursive=1")
            packages = self.packages_from_tree(json.loads(raw))
        except Exception as error:
            if not cache.exists():
                raise
            return self.packages_from_tree(json.loads(cache.read_bytes())), str(error)
        atomic_write(cache, raw)
        return packages, ""

    def blob(self, package: dict, signature: bool = False) -> bytes:
        expected = package["sig_sha" if signature else "sha"]
        cache = self.data / "cache" / expected
        if cache.exists():
            content = cache.read_bytes()
            if git_hash(content) == expected:
                return content
        path = package["path"] + (".sig" if signature else "")
        url = f"https://raw.githubusercontent.com/{REPO}/{package['revision']}/{urllib.parse.quote(path)}"
        content = self.request(url, limit=8 * 1024 * 1024)
        if git_hash(content) != expected:
            raise ValueError(f"Repository checksum mismatch: {path}")
        atomic_write(cache, content)
        return content

    def download_packages(self, packages: list[dict], progress=lambda name: None) -> Path:
        if not packages:
            raise ValueError("No packages selected.")

        def fetch(package):
            return package, self.blob(package), self.blob(package, signature=True)

        downloaded = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(fetch, package) for package in packages]
            for future in concurrent.futures.as_completed(futures):
                item = future.result()
                downloaded.append(item)
                progress(item[0]["name"])

        runs = self.data / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix=time.strftime("%Y%m%d-%H%M%S-"), dir=runs))
        # Each execution gets a new folder, so previously selected YAML cannot leak in.
        for package, yaml, signature in sorted(downloaded, key=lambda item: item[0]["name"]):
            atomic_write(folder / package["name"], yaml)
            atomic_write(folder / (package["name"] + ".sig"), signature)
        atomic_write(folder / "selection.json", json.dumps({
            "repository": PROJECT_URL, "packages": packages,
        }, ensure_ascii=False, indent=2).encode("utf-8"))
        return folder

    def download_cli(self) -> Path:
        release = json.loads(self.request(API + "/releases/latest"))
        asset = next((a for a in release.get("assets", []) if a["name"].lower() == "optimizernxt.exe"), None)
        if not asset:
            raise ValueError("The latest official release has no optimizerNXT.exe asset.")
        url = asset["browser_download_url"]
        if not url.startswith(PROJECT_URL + "/releases/download/"):
            raise ValueError("Unexpected release download URL.")
        digest = asset.get("digest") or ""
        match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})", digest)
        if not match:
            match = re.search(r"SHA256\s*:\s*([0-9a-fA-F]{64})\b", release.get("body") or "", re.I)
        if not match:
            raise ValueError("No published SHA-256 checksum found for the CLI.")
        content = self.request(url)
        if hashlib.sha256(content).hexdigest() != match.group(1).lower():
            raise ValueError("CLI SHA-256 mismatch. The executable was not saved.")
        if not content.startswith(b"MZ"):
            raise ValueError("The release asset is not a Windows executable.")
        path = self.data / "bin" / "optimizerNXT.exe"
        atomic_write(path, content)
        return path


def run_cli(executable: Path, folder: Path, started=lambda: None, auto_close=True) -> int:
    return run_host(folder, ['--exe', str(executable.resolve(strict=True))], started, auto_close)


def run_host(folder: Path, args, started=lambda: None, auto_close=True):
    from rollback import user_sid
    python = Path(sys.executable)
    if python.name.lower() == 'pythonw.exe':
        python = python.with_name('python.exe')
    command = [str(BASE / 'runner.py'), '--folder', str(folder.resolve(strict=True)), '--sid', user_sid(), *args]
    if auto_close:
        command.append('--auto-close')
    return run_program(python, command, folder, started, console=True)


def run_program(executable: Path, args: list[str], folder: Path, started=lambda: None,
                console=False, wait=True) -> int:
    if os.name != "nt":
        raise OSError("Windows is required.")
    executable = executable.resolve(strict=True)
    folder = folder.resolve(strict=True)
    arguments = subprocess.list2cmdline(args)
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.IsUserAnAdmin.restype = wintypes.BOOL
    if shell.IsUserAnAdmin():
        process = subprocess.Popen([str(executable), *args], cwd=folder,
                                   creationflags=subprocess.CREATE_NEW_CONSOLE if console else 0)
        started()
        return process.wait() if wait else 0

    class SHELLEXECUTEINFOW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("fMask", ctypes.c_ulong),
                    ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR),
                    ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p),
                    ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY),
                    ("dwHotKey", wintypes.DWORD), ("hIcon", wintypes.HANDLE),
                    ("hProcess", wintypes.HANDLE)]

    info = SHELLEXECUTEINFOW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x40  # SEE_MASK_NOCLOSEPROCESS: retain a handle to wait for this run.
    info.lpVerb = "runas"
    info.lpFile = str(executable)
    info.lpParameters = arguments
    info.lpDirectory = str(folder)
    info.nShow = 1
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFOW)]
    shell.ShellExecuteExW.restype = wintypes.BOOL
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    try:
        started()
        if not wait:
            return 0
        if kernel.WaitForSingleObject(info.hProcess, 0xFFFFFFFF) == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value
    finally:
        kernel.CloseHandle(info.hProcess)
