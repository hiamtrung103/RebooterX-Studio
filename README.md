# RebooterX Studio

A bilingual Windows desktop interface for the official [OptimizerNXT YAML hub](https://github.com/hellzerg/optimizerNXT/blob/main/HUB.md).
Select packages, inspect their contents, and run the original CLI from one workspace.

Source: https://github.com/hiamtrung103/RebooterX-Studio

Copyright (c) Hiamtrung102 2026. Independent from OptimizerNXT and NVIDIA.

## Features

- English and Vietnamese, light and dark themes.
- Five destinations: Windows, Tools, NVIDIA, Activity and Settings. NVIDIA has its
  own full-page profile editor; package categories live in the Windows filter.
- Previously applied packages have a green outline and a protruding Installed
  badge. Older revisions have their own label. Records survive restarts; a
  successful restore removes the applied marker. This is execution history,
  not a live scan of Windows settings.
- Larger navigation and package text, a spring-driven glass selection lens and animated glass buttons.
- The navigation lens has soft capsule lighting with no stroked border. Hold the
  selected lens and drag vertically; releasing snaps to the nearest tab. Escape or
  focus loss cancels the drag. Click and keyboard navigation remain available.
- Coalesced wheel/scrollbar events. Native repaint repair runs after scrolling
  settles, without a synchronous redraw/erase of every child on each frame.
- Navigation reuses canvas items, captions and lens images while moving, with
  softer capsule lighting and a lighter shadow.
- Search ignores Vietnamese accents; selections remain visible in a dedicated view.
- Read package descriptions, compatibility, important consequences and original YAML.
- Download YAML together with its `.sig` from the same upstream commit.
- Check Git blob hashes for package downloads and published SHA-256 for the CLI.
- Apply only selected packages, in a fresh folder for each run. The upstream CLI
  verifies the actual package signatures and requests Windows administrator access.
- Separate download-only action, CLI path selection and activity history for the session.
- Bilingual usage instructions and context/tradeoffs for all 28 known packages.
- Live RAM usage and official Mem Reduct portable download, opening and explicit one-time cleanup.
- NVIDIA game/global profiles through the installed driver's public NVAPI:
  power management, shader cache size and texture filtering quality, with previews,
  local backups and verified restore. Launch NVIDIA App / Control Panel separately.
- GitHub and information buttons identify public source, downloads and verification limits.

## Run

**Portable onefile EXE:** download `RebooterX-Studio.exe` from
[Releases](https://github.com/hiamtrung103/RebooterX-Studio/releases). It runs on
64-bit Windows 10/11 without Python or a separate library folder. Windows requests
administrator approval at startup (`requireAdministrator` manifest plus a runtime
check). Cancelling UAC prevents the app from starting. No tweaks are auto-applied.
The separately downloaded OptimizerNXT CLI still needs its required .NET runtime.

Packaged settings/history/backups live in `%LOCALAPPDATA%\RebooterX-Studio`, outside
the temporary onefile extraction directory. Source runs keep using `data/` beside
the source. `REBOOTERX_DATA_DIR` can select an existing data folder for either
version; retain that folder to preserve historical status and rollback backups.

**Run from source:** requires Windows and Python 3.10+ with Tkinter. Source launches
also request administrator approval before opening the UI.

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

### HTTPS on shared / internet-cafe PCs

Version 2.3.1 uses Windows native certificate-chain verification through
`truststore`, with a bundled Mozilla public CA bundle from `certifi`. This also
supports roots trusted by Windows-managed proxies and missing intermediate-chain
retrieval. Server certificates and hostnames are always verified; TLS 1.2 is the
minimum. No Windows certificate store is changed. One cached context is shared by
download workers to avoid rebuilding the trust configuration for every file.

Certificate verification errors stop immediately rather than repeating the same
failure three times, and show actionable bilingual advice. If verification still
fails, check Windows date/time, Windows certificate updates and the venue's HTTPS
proxy with the venue administrator. This update cannot repair an untrusted proxy
certificate or an incorrect machine clock remotely.

For a read/download-only diagnostic, run the packaged executable with
`--network-test C:\path\network-report.json`. It checks GitHub API, raw content
and an official CLI download with SHA-256 verification; it never executes the CLI.
RAM polling/painting pauses while the Tools page is hidden or the app is minimized.

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

In the dedicated **NVIDIA** tab, select a game executable (NVIDIA matches its
filename) or explicitly choose global settings. Tick the settings to change, then
use **Read / preview → Apply**. The performance preset fills **Prefer maximum
performance**, **Unlimited**, and **High performance**, plus the optional driver
settings below; it does not apply anything
until you review it. Existing profiles may be shared by several executables; the
preview shows their count. Shader Cache Size is always global, including in game
mode. Unlimited uses disk space, not VRAM. Higher power draw, heat and reduced
texture quality are possible; measure frame times and FPS on your hardware.

Additional controls and preset values:

| Driver setting | Performance preset | Scope / tradeoff |
| --- | --- | --- |
| Vertical sync | Off | May remove a refresh-rate limit; allows tearing; review separately for G-SYNC |
| Max Frame Rate | Off | Removes the driver cap, not in-game/other caps; optional FPS limits remain available |
| Anisotropic sample optimization | On | DirectX; possible texture-quality tradeoff |
| Trilinear optimization | On | DirectX; high-quality texture mode may ignore it |
| Threaded optimization | Auto | OpenGL; forcing On can regress some games |
| Antialiasing - FXAA | Off | Removes driver FXAA; possible jagged edges; in-game AA is separate |
| Preferred refresh rate | Highest available | Requests display Hz, not more rendered FPS; may be unavailable with VRR |

There is no guaranteed FPS increase. The page includes manual guides for NIS
(lower-resolution upscaling), Low Latency Mode, in-game Reflex and Full-screen
scaling. Reflex is a latency feature and overrides the driver low-latency mode.
NVIDIA does not expose Low Latency Mode through the public NVAPI SDK used here,
so the app guides the user to Control Panel instead of writing undocumented IDs.
References: [NVIDIA Control Panel help](https://www.nvidia.com/content/Control-Panel-Help/vLatest/en-us/mergedProjects/3D%20Settings/Manage_3D_Settings_%28reference%29.htm),
[latency guide](https://www.nvidia.com/en-us/geforce/guides/system-latency-optimization-guide/),
[NVAPI guidance](https://forums.developer.nvidia.com/t/low-latency-mode-setting/241104).
Trilinear's inverted SDK flag is cross-checked against
[Profile Inspector's metadata](https://github.com/Orbmu2k/nvidiaProfileInspector/blob/master/nvidiaProfileInspector/CustomSettingNames.xml).

The adapter uses the installed `nvapi64.dll` / `nvapi.dll` from Windows System32,
with ABI and constants from [NVIDIA's public SDK](https://github.com/NVIDIA/nvapi).
No external driver/profile editor is downloaded. Unsupported driver settings and
missing NVIDIA GPUs report errors. If NVAPI returns permission error -137, restart
Studio as administrator. All chosen changes are staged in one driver session;
the session is saved only after every setting is accepted and the local backup
is written. Applied settings are read back in a fresh session for verification.

Backups live in `data/nvidia-backups`. **Restore last change** restores previous
explicit values or removes our override to return to inherited/default values.
Restore stops if any target value/profile changed after applying. A newly created
game profile/application association remains after its settings are restored.
These backups are separate from OptimizerNXT's package history.

**Full-screen scaling is manual**: use the included instructions and Control Panel
button: Adjust desktop size and position → select monitor → Full-screen → GPU →
optionally Override the scaling mode → Apply. This can stretch other aspect ratios.
The game's own Fullscreen mode is configured inside the game. Studio does not
automatically set display scaling or the legacy image-preview Performance slider;
the latter is separate from the advanced 3D profile settings above.

NVIDIA write/restore behavior is covered by simulated driver tests. The development
machine exposes Intel UHD and a virtual display, so real NVIDIA driver writes have
not been hardware-tested here.

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
cancellation, five-item navigation, scrolling/dragging, glass animation and resizing in both languages.

Build the administrator-only onefile executable with `powershell -File Build.ps1`.
The build runs the tests and uses the checked-in PyInstaller spec. It bundles Tk,
CustomTkinter themes/fonts/icons, Pillow, YAML, pywin32 and the internal console
runner. The upstream optimizer and Mem Reduct remain separate optional downloads.

## Credits And License

Studio is an independent interface, not an official OptimizerNXT release. Its UI is
implemented with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), with
[Lucide](https://lucide.dev) icons. See `assets/LUCIDE-LICENSE`.

The Studio source is MIT-licensed. Separately downloaded OptimizerNXT, Mem Reduct
and upstream packages retain their own licenses. The reference application's private
source, assets, fonts and credentials are not included.
