"""Plain-language context alongside the exact upstream YAML preview."""
GUIDANCE = {
    'add-open-cmd': (
        'Useful when working with command-line tools in a folder. Adds a shortcut; it does not speed up Windows.',
        'Hữu ích khi cần chạy lệnh ngay trong một thư mục. Chỉ thêm lối tắt, không làm Windows chạy nhanh hơn.'),
    'add-take-ownership': (
        'Useful for files blocked by ownership permissions. Only use the new menu on files you understand: changing system-file permissions can break servicing or weaken access controls.',
        'Dùng khi không truy cập được file do quyền sở hữu. Chỉ dùng menu mới với file bạn hiểu rõ: đổi quyền file hệ thống có thể làm lỗi cập nhật hoặc giảm bảo vệ truy cập.'),
    'disable-auto-updates': (
        'Useful when you need to control update timing. Security fixes and Store apps will need manual attention; this does not remove already installed updates.',
        'Dùng khi muốn chủ động thời điểm cập nhật. Bạn phải tự theo dõi bản vá bảo mật và ứng dụng Store; gói này không gỡ các bản cập nhật đã cài.'),
    'disable-chrome-telemetry': (
        'Useful if you do not want Chrome diagnostic reports. Reduces reporting rather than guaranteeing better FPS or anonymous browsing.',
        'Dùng khi không muốn Chrome gửi báo cáo chẩn đoán. Mục tiêu là giảm báo cáo, không bảo đảm tăng FPS hay duyệt web ẩn danh.'),
    'disable-copilot': (
        'Useful for local Windows search without AI/web suggestions. Copilot, Cortana and online search features may become unavailable.',
        'Dùng khi chỉ muốn tìm kiếm cục bộ, ít gợi ý AI/web. Copilot, Cortana và các tính năng tìm kiếm trực tuyến có thể không còn dùng được.'),
    'disable-edge-telemetry': (
        'Also disables SmartScreen in Edge. Consider the loss of dangerous-site/download checks before choosing this package for privacy.',
        'Gói này còn tắt SmartScreen của Edge. Cân nhắc việc mất kiểm tra website và tải xuống nguy hiểm trước khi chọn chỉ vì mục đích riêng tư.'),
    'disable-firefox-telemetry': (
        'Useful for reducing Firefox diagnostics and background reporting. Firefox may offer less diagnostic information when troubleshooting.',
        'Dùng để giảm báo cáo chẩn đoán và tác vụ báo cáo nền của Firefox. Khi xử lý lỗi, thông tin chẩn đoán có thể ít hơn.'),
    'disable-modern-standby': (
        'Consider only for sleep/wake problems or unwanted idle drain. It cannot add S3 sleep if firmware does not support it; some devices may lose their usable sleep mode.',
        'Chỉ cân nhắc khi gặp lỗi ngủ/đánh thức hoặc hao pin lúc chờ. Gói không tạo được S3 nếu firmware không hỗ trợ; một số máy có thể mất chế độ ngủ đang dùng.'),
    'disable-nvidia-telemetry': (
        'Targets NVIDIA reporting services/tasks. It does not configure game profiles, NVIDIA App or Control Panel and does not promise higher frame rates.',
        'Tác động tới dịch vụ/tác vụ báo cáo NVIDIA. Không thiết lập profile game, NVIDIA App hay Control Panel và không bảo đảm tăng FPS.'),
    'disable-office-telemetry': (
        'Read the YAML if you use Office add-ins or business integrations. The package includes restrictions beyond diagnostic reporting, so test your Office workflow afterwards.',
        'Hãy xem YAML nếu dùng add-in hoặc tích hợp Office trong công việc. Gói có các hạn chế ngoài báo cáo chẩn đoán; cần kiểm tra lại quy trình Office sau khi chạy.'),
    'disable-smartscreen': (
        'Removes warning/check layers for apps, downloaded attachments and phishing. This is a security tradeoff, not a general performance optimization.',
        'Giảm các lớp cảnh báo/kiểm tra ứng dụng, file tải xuống và lừa đảo. Đây là đánh đổi bảo mật, không phải tinh chỉnh hiệu năng nên áp dụng chung.'),
    'disable-sticky-keys': (
        'Useful when repeated Shift presses interrupt games. Avoid if you rely on accessibility keyboard assistance.',
        'Hữu ích khi nhấn Shift liên tục làm hiện hộp thoại lúc chơi game. Không nên dùng nếu bạn cần các tính năng hỗ trợ bàn phím.'),
    'disable-superfetch': (
        'Consider when troubleshooting sustained SysMain disk activity. Windows normally uses RAM for useful caching; disabling it can make app launches slower.',
        'Cân nhắc khi điều tra tình trạng SysMain dùng ổ đĩa kéo dài. Windows dùng RAM để lưu đệm hữu ích; tắt có thể khiến mở ứng dụng chậm hơn.'),
    'disable-system-restore': (
        'Deletes existing restore snapshots as well as disabling future restore points. Deleted snapshots cannot be recovered by this app; make a separate backup first.',
        'Xóa bản chụp khôi phục hiện có và tắt tạo điểm khôi phục về sau. App không thể lấy lại bản chụp đã xóa; cần có bản sao lưu riêng trước.'),
    'disable-tablet-features': (
        'Suitable for a keyboard/mouse desktop that does not need handwriting. Avoid on pen/touch devices or if you use spelling and typing assistance.',
        'Phù hợp máy dùng chuột/bàn phím, không cần viết tay. Tránh dùng trên máy bút/cảm ứng hoặc khi cần kiểm tra chính tả và hỗ trợ nhập liệu.'),
    'disable-telemetry-services': (
        'Useful for reducing Windows diagnostic reporting. Some troubleshooting and feedback features may lose data; this does not block every connection to Microsoft.',
        'Dùng để giảm báo cáo chẩn đoán Windows. Một số công cụ xử lý lỗi/phản hồi có thể thiếu dữ liệu; không chặn mọi kết nối tới Microsoft.'),
    'disable-tpm-enforce': (
        'Relevant to Windows upgrade compatibility checks. It does not add TPM hardware, enable Secure Boot or make an unsupported device officially supported.',
        'Liên quan kiểm tra tương thích khi nâng cấp Windows. Không bổ sung chip TPM, không bật Secure Boot và không khiến máy thiếu chuẩn thành máy được hỗ trợ chính thức.'),
    'disable-vbs': (
        'May reduce virtualization-security overhead in some workloads. It also removes a protection layer; benchmark your own games before deciding the tradeoff is useful.',
        'Có thể giảm chi phí bảo mật ảo hóa trong một số tác vụ, đồng thời mất một lớp bảo vệ. Hãy đo trên game của bạn trước khi quyết định đánh đổi có đáng hay không.'),
    'disable-visual-studio-telemetry': (
        'For developers who want less Visual Studio reporting. Also changes concurrent-download settings; inspect the YAML if install/update behavior matters to your workflow.',
        'Dành cho người dùng Visual Studio muốn giảm báo cáo. Còn đổi cấu hình tải đồng thời; nên xem YAML nếu cách cài/cập nhật ảnh hưởng công việc.'),
    'disable-windows-defender': (
        'Only targets legacy Windows 7/8/8.1. Disables antivirus protection; do not select this as a routine gaming preset.',
        'Chỉ nhắm Windows 7/8/8.1 đời cũ. Tắt bảo vệ chống virus; không nên chọn như preset chơi game thông thường.'),
    'disable-windows-security': (
        'Broad changes to antivirus, services, tasks and logging on Windows 10/11. Protection may be reduced and some settings may be blocked by Windows. Review every YAML operation.',
        'Thay đổi rộng tới chống virus, dịch vụ, tác vụ và log trên Windows 10/11. Bảo vệ có thể giảm và Windows có thể chặn một số thiết lập. Cần xem từng thao tác trong YAML.'),
    'enable-game-mode': (
        'Useful for a gaming PC that does not need Xbox services or Game Bar capture. Includes several changes together; Xbox features/recording may stop working and GPU scheduling depends on driver support.',
        'Dùng cho máy chơi game không cần dịch vụ Xbox hoặc ghi hình Game Bar. Gồm nhiều thay đổi cùng lúc; tính năng Xbox/ghi hình có thể ngừng hoạt động, lập lịch GPU phụ thuộc driver.'),
    'enable-performance-tweaks': (
        'A mixed system preset, not a guaranteed FPS boost. It changes appearance, Explorer and network/multimedia behavior together; read the YAML and compare before/after on your own workload.',
        'Là preset hệ thống nhiều thành phần, không bảo đảm tăng FPS. Đổi đồng thời giao diện, Explorer và hành vi mạng/đa phương tiện; nên xem YAML và đo trước/sau với nhu cầu thực tế.'),
    'enhance-privacy': (
        'Useful if you prefer fewer ads and cloud suggestions. Location-dependent apps, personalized results and some cloud experiences may be limited.',
        'Dùng khi muốn bớt quảng cáo và gợi ý đám mây. Ứng dụng cần vị trí, kết quả cá nhân hóa và một số trải nghiệm đám mây có thể bị hạn chế.'),
    'exclude-drivers': (
        'Useful when maintaining a known working GPU/device driver. You must install driver updates yourself, including compatibility and security fixes.',
        'Hữu ích khi cần giữ driver GPU/thiết bị đang ổn định. Bạn phải tự cài các bản driver mới, gồm sửa lỗi tương thích và bảo mật.'),
    'simplify-windows10-11': (
        'Useful for fewer suggestions and background integrations. Cloud clipboard, Phone Link and related conveniences may stop working; this is not an app debloater for every installed program.',
        'Dùng để giảm gợi ý và tích hợp nền. Clipboard đám mây, Phone Link và tiện ích liên quan có thể ngừng hoạt động; không phải công cụ gỡ mọi ứng dụng có sẵn.'),
    'simplify-windows11': (
        'For a simpler Windows 11 desktop. Snap assistance and taskbar conveniences may disappear; avoid if you use guided window snapping frequently.',
        'Dành cho giao diện Windows 11 đơn giản hơn. Hỗ trợ chia cửa sổ và tiện ích taskbar có thể mất; cân nhắc nếu thường dùng gợi ý Snap.'),
    'uninstall-onedrive': (
        'For PCs that do not use OneDrive. Finish syncing and keep a local copy of needed files first; online-only files need downloading before OneDrive is removed.',
        'Dành cho máy không dùng OneDrive. Hoàn tất đồng bộ và giữ bản cục bộ của file cần thiết trước; file chỉ có trên cloud cần tải về trước khi gỡ.'),
}

COPY = {
    'windows_nav': ('Windows', 'Windows'),
    'tools': ('Tools', 'Công cụ'),
    'tools_meta': ('Memory & graphics', 'Bộ nhớ & đồ họa'),
    'github': ('GitHub', 'GitHub'),
    'about': ('About & source code', 'Thông tin & mã nguồn'),
    'help': ('Instructions', 'Hướng dẫn sử dụng'),
    'context': ('When to use & tradeoffs', 'Khi nào dùng & đánh đổi'),
    'help_text': (
        '1. Windows: filter or search, then click a package to read its details and unchanged YAML. Check only the packages you need.\n\n2. Download saves YAML + signatures without applying changes. Run selected opens a review, then the official CLI with Windows administrator approval. Read the CLI results; a zero exit code does not prove each tweak succeeded.\n\n3. Make a backup or restore point before applying changes. Restart when required. There is no automatic undo, and packages that disable protection or delete restore points need particular care.\n\n4. Tools: download verified Mem Reduct, open its own settings, or explicitly request a one-time cleanup. Cleanup is never scheduled by this app.\n\n5. NVIDIA: open the installed app/panel. For game-specific changes, add the game executable under Program Settings and measure performance before/after. Driver profiles are edited in NVIDIA tools.',
        '1. Windows: lọc hoặc tìm kiếm, bấm vào gói để đọc mô tả và YAML gốc. Chỉ tích các gói thực sự cần.\n\n2. Tải xuống chỉ lưu YAML + chữ ký, chưa thay đổi máy. Chạy đã chọn mở bảng xem lại, rồi chạy CLI chính thức sau khi bạn chấp thuận quyền quản trị Windows. Đọc kết quả ở CLI; mã thoát 0 không chứng minh từng tinh chỉnh đều thành công.\n\n3. Sao lưu hoặc tạo điểm khôi phục trước khi chạy. Khởi động lại khi cần. Không có hoàn tác tự động; cần đặc biệt cân nhắc gói tắt bảo vệ hoặc xóa điểm khôi phục.\n\n4. Công cụ: tải Mem Reduct đã kiểm tra mã băm, mở cài đặt riêng của nó hoặc chủ động dọn một lần. App này không lên lịch tự dọn RAM.\n\n5. NVIDIA: mở ứng dụng/bảng điều khiển đã cài. Với từng game, thêm file game trong Program Settings và đo hiệu năng trước/sau. Chỉnh profile driver trong công cụ NVIDIA.'),
    'about_text': (
        'RebooterX Studio 2.0\n© Hiamtrung102 2026\n\nThe complete source code of this app is public on GitHub. The app does not implement cryptocurrency mining, credential theft or remote control. It does not upload your selections or activity logs. Public source alone is not a security certification.\n\nWindows tweaks are unchanged YAML from hellzerg/optimizerNXT, applied by its official CLI. Mem Reduct is a separate open-source program by Henry++. Downloads contact GitHub and are checked against upstream hashes; Mem Reduct signatures are preserved, not cryptographically verified here. Review external code and operations too.\n\nThis is an independent interface, not an official OptimizerNXT or NVIDIA product.',
        'RebooterX Studio 2.0\n© Hiamtrung102 2026\n\nToàn bộ mã nguồn của app này được công khai trên GitHub. App không triển khai đào coin, lấy cắp thông tin đăng nhập hay điều khiển từ xa. Không tải lựa chọn hoặc nhật ký hoạt động của bạn lên mạng. Mã nguồn công khai tự nó không phải chứng nhận an toàn.\n\nCác tinh chỉnh Windows là YAML gốc từ hellzerg/optimizerNXT, chạy bằng CLI chính thức của dự án đó. Mem Reduct là chương trình nguồn mở riêng của Henry++. File tải từ GitHub được kiểm tra theo mã băm phía nguồn; giữ kèm chữ ký Mem Reduct nhưng không xác minh chữ ký mật mã tại đây. Cần xem cả mã nguồn và thao tác của công cụ ngoài.\n\nĐây là giao diện độc lập, không phải sản phẩm chính thức của OptimizerNXT hay NVIDIA.'),
    'memory_title': ('Mem Reduct', 'Mem Reduct'),
    'memory_note': (
        'Download the official portable build (requires 7-Zip). SHA-256 is checked for both archive and executable. Open Mem Reduct to configure its own settings. One-time cleanup requires administrator approval and may cause temporary stutter; less used RAM does not automatically mean better FPS.',
        'Tải bản portable chính thức (cần 7-Zip). Kiểm tra SHA-256 của cả gói nén và file chạy. Mở Mem Reduct để chỉnh cài đặt riêng. Dọn một lần cần chấp thuận quyền quản trị, có thể gây khựng tạm thời; RAM dùng ít hơn không đồng nghĩa FPS cao hơn.'),
    'memory_download': ('Download / update', 'Tải / cập nhật'),
    'memory_open': ('Open Mem Reduct', 'Mở Mem Reduct'),
    'memory_clean': ('Clean once', 'Dọn một lần'),
    'memory_full': ('Full cleanup', 'Dọn toàn bộ'),
    'memory_confirm': ('Run a one-time memory cleanup with Mem Reduct? Applications may need to reload cached data. Full cleanup can cause noticeable stutter. No automatic cleanup will be configured.',
                       'Dọn bộ nhớ một lần bằng Mem Reduct? Ứng dụng có thể cần nạp lại dữ liệu đệm. Dọn toàn bộ có thể gây khựng rõ rệt. Không thiết lập tự động dọn.'),
    'memory_ready': ('Portable build verified', 'Đã xác minh bản portable'),
    'memory_missing': ('Mem Reduct not downloaded', 'Chưa tải Mem Reduct'),
    'memory_done': ('Mem Reduct finished · exit code {code}', 'Mem Reduct hoàn tất · mã thoát {code}'),
    'ram': ('{used:.1f} / {total:.1f} GB used · {available:.1f} GB available', 'Đã dùng {used:.1f} / {total:.1f} GB · Khả dụng {available:.1f} GB'),
    'nvidia_title': ('NVIDIA · Game profiles', 'NVIDIA · Cấu hình game'),
    'nvidia_note': ('NVIDIA App: Graphics → select a game → Driver Settings. Control Panel: Manage 3D settings → Program Settings → Add the game .exe → Apply. Start with one setting at a time and compare frame time as well as FPS. This version opens installed NVIDIA tools; it does not write driver profiles.',
                    'NVIDIA App: Graphics → chọn game → Driver Settings. Control Panel: Manage 3D settings → Program Settings → Add file .exe của game → Apply. Đổi từng thiết lập rồi so sánh cả frame time và FPS. Phiên bản này mở công cụ NVIDIA đã cài, chưa ghi profile driver.'),
    'nvidia_app': ('NVIDIA App', 'NVIDIA App'),
    'nvidia_panel': ('NVIDIA Control Panel', 'NVIDIA Control Panel'),
    'nvidia_missing': ('The NVIDIA tool was not found. Install it from NVIDIA or Microsoft Store, then retry.', 'Không tìm thấy công cụ NVIDIA. Cài từ NVIDIA hoặc Microsoft Store rồi thử lại.'),
    'seven_zip': ('7-Zip', '7-Zip'),
}
