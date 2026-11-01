# OptimizerNXT Studio

A bilingual Windows desktop interface for the official [OptimizerNXT YAML hub](https://github.com/hellzerg/optimizerNXT/blob/main/HUB.md).
Select packages, inspect their contents, and run the original CLI from one workspace.

## Features

- English and Vietnamese, light and dark themes.
- Categories for performance, privacy, Windows/apps and security.
- Search ignores Vietnamese accents; selections remain visible in a dedicated view.
- Read package descriptions, compatibility, important consequences and original YAML.
- Download YAML together with its `.sig` from the same upstream commit.
- Check Git blob hashes for package downloads and published SHA-256 for the CLI.
- Apply only selected packages, in a fresh folder for each run. The upstream CLI
  verifies the actual package signatures and requests Windows administrator access.
- Separate download-only action, CLI path selection and activity history for the session.

## Run

Requires Windows, Python 3.10+ with Tkinter and the .NET runtime required by OptimizerNXT.

1. Run `Setup.cmd` once to create a local environment and install dependencies.
2. Open `Start.cmd`.
3. Download the official CLI in **Settings**, or browse to a copy you already have.
4. Select packages and choose **Run selected**. Review the list and accept Windows UAC.
5. Read the CLI console for results. The CLI may wait for a key before closing.

Alternatively:

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Tiếng Việt

1. Chạy `Setup.cmd` một lần để cài thư viện, rồi mở `Start.cmd`.
2. Trong **Cài đặt**, tải CLI chính thức hoặc chọn file `optimizerNXT.exe` đã có.
3. Chọn nhóm bên trái, tick các gói cần dùng. Bấm một gói để xem mô tả và YAML.
4. Chọn **Chạy đã chọn**, xem lại danh sách và chấp nhận UAC của Windows.
5. Đọc kết quả ở cửa sổ CLI. CLI có thể cần nhấn phím trước khi đóng.

Nút **Tải xuống** chỉ tải file, không thay đổi thiết lập Windows. Ngôn ngữ, giao diện,
đường dẫn CLI và lựa chọn được lưu cho lần sau. Không có gói nào được chọn mặc định
ở lần mở đầu tiên.

## Package Behavior

Packages run intact. Selecting individual steps inside a YAML file or merging
packages would invalidate their signatures, so Studio does neither. The downloaded
YAML is authoritative; translated summaries describe the known upstream packages.

Some packages disable security, updates or synchronization, or delete restore points.
Consequences are displayed in the inspector and review dialog. There is no automatic
undo. For example, `enable-game-mode` also disables Xbox/Game Bar/DVR, while the Edge
telemetry package also changes SmartScreen.

Studio does not interpret the CLI's exit code as proof that every tweak succeeded.
Check the upstream console/log output for each operation. A running CLI remains
independent if you close Studio.

## Local Data

`data/` stores settings, the official CLI, cached blobs, and per-run package folders.
It is excluded from Git. Override its location with `OPTIMIZERNXT_DATA_DIR` when needed.
No binaries, downloaded YAML packages or personal settings are distributed in this repo.

## Development

```powershell
python -m unittest discover -s tests -v
```

Backend tests use mocked downloads and temporary directories. UI tests use an isolated
data folder and mock CLI execution; they never apply Windows tweaks.

## Credits And License

Studio is an independent interface, not an official OptimizerNXT release. Its UI is
implemented with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), with
[Lucide](https://lucide.dev) icons. See `assets/LUCIDE-LICENSE`.

The Studio source is MIT-licensed. The separately downloaded OptimizerNXT executable
and upstream packages retain their own licenses. The reference application's private
source, assets, fonts and credentials are not included.
