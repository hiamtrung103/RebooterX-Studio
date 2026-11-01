# RebooterX Studio

A bilingual Windows desktop interface for the official [OptimizerNXT YAML hub](https://github.com/hellzerg/optimizerNXT/blob/main/HUB.md).
Select packages, inspect their contents, and run the original CLI from one workspace.

Source: https://github.com/hiamtrung103/RebooterX-Studio

Copyright (c) Hiamtrung102 2026. Independent from OptimizerNXT and NVIDIA.

## Features

- English and Vietnamese, light and dark themes.
- Four destinations: Windows, Tools, Activity and Settings. Package categories live in the Windows filter.
- Larger navigation and package text, a spring-driven glass selection lens and animated glass buttons.
- The navigation lens has soft capsule lighting with no stroked border. Hold the
  selected lens and drag vertically; releasing snaps to the nearest tab. Escape or
  focus loss cancels the drag. Click and keyboard navigation remain available.
- Paced wheel/scrollbar handling and explicit Windows child-window repainting.
- Search ignores Vietnamese accents; selections remain visible in a dedicated view.
- Read package descriptions, compatibility, important consequences and original YAML.
- Download YAML together with its `.sig` from the same upstream commit.
- Check Git blob hashes for package downloads and published SHA-256 for the CLI.
- Apply only selected packages, in a fresh folder for each run. The upstream CLI
  verifies the actual package signatures and requests Windows administrator access.
- Separate download-only action, CLI path selection and activity history for the session.
- Bilingual usage instructions and context/tradeoffs for all 28 known packages.
- Live RAM usage and official Mem Reduct portable download, opening and explicit one-time cleanup.
- Launch installed NVIDIA App / Control Panel with guidance for per-game settings.
- GitHub and information buttons identify public source, downloads and verification limits.

## Run

Requires Windows, Python 3.10+ with Tkinter and the .NET runtime required by OptimizerNXT.

1. Run `Setup.cmd` once to create a local environment and install dependencies.
2. Open `Start.cmd`.
3. Download the official CLI in **Settings**, or browse to a copy you already have.
4. Select packages and choose **Run selected**. Review the list and accept Windows UAC.
5. Read per-package results in Studio. The optimizer console closes automatically;
   turn this off in Settings to keep the final summary open.

Alternatively:

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Tiếng Việt

1. Chạy `Setup.cmd` một lần để cài thư viện, rồi mở `Start.cmd`.
2. Trong **Cài đặt**, tải CLI chính thức hoặc chọn file `optimizerNXT.exe` đã có.
3. Vào **Windows**, chọn nhóm trong bộ lọc, tích các gói cần dùng. Bấm một gói để xem tác dụng, đánh đổi và YAML.
4. Chọn **Chạy đã chọn**, xem lại danh sách và chấp nhận UAC của Windows.
5. Xem kết quả từng gói trong tool. Mặc định cửa sổ optimizer tự đóng;
   có thể tắt trong Cài đặt để giữ cửa sổ tổng kết.

Nút **Tải xuống** chỉ tải file, không thay đổi thiết lập Windows. Ngôn ngữ, giao diện,
đường dẫn CLI và lựa chọn được lưu cho lần sau. Không có gói nào được chọn mặc định
ở lần mở đầu tiên.

Trong **Công cụ**, xem RAM khả dụng, tải/mở Mem Reduct hoặc dọn bộ nhớ một lần sau
khi xác nhận. Bản portable cần [7-Zip](https://www.7-zip.org/) để giải nén; nếu thiếu,
app báo rõ và không chạy công cụ. Nút **Hướng dẫn sử dụng** giải thích quy trình đầy đủ.
Footer hiển thị **© Hiamtrung102 2026**, nút GitHub mở repo này và nút **i** nêu phạm vi mã nguồn.

## Memory And Graphics

Mem Reduct is downloaded separately from [Henry++'s official releases](https://github.com/henrypp/memreduct/releases).
The release's SHA-256 manifest must match both the archive and the executable for the
native architecture. 7-Zip extracts only the named portable files. The executable is
checked against the saved receipt on each launch. This detects accidental changes;
it is not independent publisher authentication. The `.sig` is preserved, but this app
does not perform GPG verification. Mem Reduct retains its GPL-3.0 license and source.
No Mem Reduct binary is included in this repository.

**Download / update** installs the portable files without running them. **Open Mem Reduct**
opens the original application with administrator approval. **Clean once** invokes
`-clean`; **Full cleanup** invokes `-clean:full`, each after an explicit confirmation.
RebooterX does not configure scheduled/automatic cleanup. Cleaning can cause stutter
or reload cached data; lower RAM usage does not guarantee higher game performance.

The NVIDIA section opens tools already installed on the PC. In NVIDIA App, select
Graphics, the game and Driver Settings. In Control Panel, use Manage 3D settings,
Program Settings, add the game executable, change one setting, and Apply. Compare
frame times and FPS on your own hardware. This version does not edit driver profiles.

## Package Behavior

Packages run intact. Selecting individual steps inside a YAML file or merging
packages would invalidate their signatures, so Studio does neither. The downloaded
YAML is authoritative; translated summaries describe the known upstream packages.

Some packages disable security, updates or synchronization, or delete restore points.
Consequences are displayed in the inspector and review dialog. Rollback is limited to
supported packages with a complete pre-run snapshot. For example, `enable-game-mode` also disables Xbox/Game Bar/DVR, while the Edge
telemetry package also changes SmartScreen.

Studio does not interpret the CLI's exit code as proof that every tweak succeeded.
Check the upstream console/log output for each operation. A running CLI remains
independent if you close Studio.

## Local History And Restore

Each selected package executes separately with its unchanged YAML and signature. An
isolated copy of the chosen CLI writes logs under that package's run folder. The host
releases the CLI's final `ReadKey` only after its log reports `Exiting.`; it never sends
keyboard input to other windows. The host closes automatically by default. Settings
can keep the final summary open instead. No executable or YAML is patched.

`data/history.json` records the last attempt, exact YAML blob hash, timestamp, previous
completed runs and pending run folders. `run-result.json` and per-package `.log` files
remain in `data/runs/`. Restarting Studio imports available results from pending runs,
including runs that finished after the UI closed. Downloading alone never marks a
package applied. A completed stage with verified YAML, executed steps and no reported
warnings/errors gets **Applied / Đã chạy**; errors, skipped steps, incomplete logs and
older package revisions have separate states. This is execution evidence, not a scan
of current Windows settings. Older unrecorded runs are not inferred from selections.
Successful packages are unchecked to avoid accidental repeats; explicitly rechecking
allows another run. Use the Windows filter **Previously applied / Gói đã chạy**.

**Restore previous settings / Khôi phục thiết lập trước** is enabled only when a
complete, sealed snapshot exists. Supported packages contain only understood registry
steps under HKCU/HKLM, and all target keys must already exist and be readable. Before
execution, Windows `RegSaveKey` saves the affected subtrees, including permissions.
After execution, fingerprints include values, subkeys, owners and DACLs. Restore checks
the backup checksum, Windows user and all current fingerprints before any write.
Changed state blocks automatic restore rather than overwriting subsequent user/driver
changes. `RegRestoreKey` uses no force flag; Windows may refuse keys that are in use.
Failures remain visible and backups remain local. A restart may be required.

There is no guessed inverse for scripts, service combinations, removed applications,
deleted restore points, missing pre-run backups or unsupported operations. A pure
registry package such as `disable-vbs` may support restore when its existing keys can
be backed up; `uninstall-onedrive` and `disable-system-restore` do not. Always inspect
the actual availability shown after the run. Keep separate backups for wider recovery.

## Local Data

`data/` stores settings, the official CLI, cached blobs, and per-run package folders.
It is excluded from Git. Override its location with `REBOOTERX_DATA_DIR` when needed
(the older `OPTIMIZERNXT_DATA_DIR` variable remains supported).
No binaries, downloaded YAML packages or personal settings are distributed in this repo.

## Source And Network Behavior

All RebooterX Studio application source is public in this repo. It does not implement
mining, credential collection or remote control, and does not upload activity logs or
selections. GitHub requests download the catalog, selected YAML/signatures, the official
CLI and Mem Reduct releases. External links open in your default browser. Public source
is reviewable, not a guarantee or an independent malware audit. Review the separately
downloaded upstream tools as well as this interface before running changes.

Liquid glass is composited locally using Pillow and a Tk canvas. It simulates highlights,
refraction-like edges and damped motion; it is not OS-level transparency through other windows.

## Development

```powershell
python -m unittest discover -s tests -v
```

Backend tests use mocked downloads and temporary directories. UI tests use an isolated
data folder and mock execution; they never apply Windows tweaks or clean memory.
The console integration test compiles a harmless C# fixture when the Windows .NET
Framework compiler is present; it exercises real console input and auto-close without
running the optimizer. Registry restoration tests mock Windows writes and verify
conflict refusal and the no-force restore call. Actual native registry restoration
must be validated separately on a disposable elevated Windows environment.
Tests cover checksum failure, architecture selection, exact cleanup arguments, confirmation
cancellation, four-item navigation, scrolling/dragging, glass animation and resizing in both languages.

## Credits And License

Studio is an independent interface, not an official OptimizerNXT release. Its UI is
implemented with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), with
[Lucide](https://lucide.dev) icons. See `assets/LUCIDE-LICENSE`.

The Studio source is MIT-licensed. Separately downloaded OptimizerNXT, Mem Reduct
and upstream packages retain their own licenses. The reference application's private
source, assets, fonts and credentials are not included.
