import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import core
from ui import StudioApp, category_for, normalize


def make_packages():
    return [{'name': name + '.yaml', 'path': 'yaml/' + name + '.yaml',
             'sha': 'b' * 40, 'sig_sha': 'c' * 40, 'revision': 'a' * 40}
            for name in ('enable-game-mode', 'enhance-privacy', 'disable-windows-security')]


class StudioUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='studio-tests-')
        self.addCleanup(self.temp.cleanup)
        self.app = StudioApp(Path(self.temp.name), autoload=False)
        self.app.withdraw()
        self.addCleanup(self.destroy_app)
        self.app.repo.blob = lambda *_args: b'jobs: []'
        self.app.packages = make_packages()
        self.app.render()
        self.app.update()

    def destroy_app(self):
        for job in self.app.tk.call('after', 'info'):
            self.app.tk.call('after', 'cancel', job)
        self.app.destroy()

    def drain(self):
        deadline = time.monotonic() + 5
        while self.app.busy and time.monotonic() < deadline:
            self.app.update()
            time.sleep(0.02)
        self.assertFalse(self.app.busy)

    def test_categories_search_and_select_visible(self):
        self.assertEqual(self.app.checked, set())
        self.app.navigate('performance')
        self.app.select_visible()
        self.assertEqual(self.app.checked, {'enable-game-mode.yaml'})
        self.app.navigate('privacy')
        self.app.query.set('rieng tu')
        self.assertEqual(list(self.app.rows), ['enhance-privacy.yaml'])
        self.app.query.set('')
        self.app.navigate('selection')
        self.assertEqual(list(self.app.rows), ['enable-game-mode.yaml'])
        self.app.clear_selection()
        self.assertEqual(self.app.visible_packages(), [])

    def test_languages_themes_and_saved_preferences(self):
        self.app.change_language('English')
        self.assertEqual(self.app.run_button.cget('text'), 'Run selected')
        self.app.change_appearance('Dark')
        self.app.change_language('Tiếng Việt')
        self.assertEqual(self.app.run_button.cget('text'), 'Chạy đã chọn')
        self.assertEqual(self.app.appearance_control.get(), 'Tối')
        saved = json.loads(self.app.settings_file.read_text(encoding='utf-8'))
        self.assertEqual((saved['language'], saved['appearance']), ('vi', 'Dark'))

    def test_run_boundary_only_checked_packages_and_cancel(self):
        self.app.checked = {'enable-game-mode.yaml'}
        self.app.exe.set(__file__)
        destination = Path(self.temp.name) / 'run'
        destination.mkdir()
        with patch.object(self.app, 'confirm_run', return_value=True), \
             patch.object(self.app.repo, 'download_packages', return_value=destination) as download, \
             patch.object(core, 'run_cli', return_value=0) as run:
            self.app.prepare(True)
            self.drain()
            self.assertEqual([p['name'] for p in download.call_args.args[0]], ['enable-game-mode.yaml'])
            run.assert_called_once()
            self.assertEqual(run.call_args.args[1], destination)
        with patch.object(self.app, 'confirm_run', return_value=False), \
             patch.object(core, 'run_cli') as run, \
             patch.object(self.app.repo, 'download_packages') as download:
            self.app.prepare(True)
            download.assert_not_called()
            run.assert_not_called()

    def test_download_never_runs_cli(self):
        self.app.checked = {'enhance-privacy.yaml'}
        destination = Path(self.temp.name) / 'run'
        destination.mkdir()
        with patch.object(self.app.repo, 'download_packages', return_value=destination), \
             patch.object(core, 'run_cli') as run:
            self.app.prepare(False)
            self.drain()
            run.assert_not_called()
        self.assertEqual(self.app.last_folder, destination)

    def test_busy_state_does_not_change_selection(self):
        self.app.checked = {'enable-game-mode.yaml'}
        self.app.set_busy(True)
        self.app.clear_selection()
        self.app.select_visible()
        self.app.toggle('enhance-privacy.yaml')
        self.assertEqual(self.app.checked, {'enable-game-mode.yaml'})
        self.assertEqual(self.app.run_button.cget('state'), 'disabled')
        self.app.set_busy(False)

    def test_stale_preview_event_is_ignored(self):
        self.app.preview_serial = 4
        self.app.preview_content = 'current'
        self.app.events.put(('preview', (3, 'stale')))
        self.app.update()
        self.app.poll()
        self.assertEqual(self.app.preview_content, 'current')

    def test_visible_resizing_in_both_languages_has_no_callback_errors(self):
        errors = []
        self.app.report_callback_exception = lambda *args: errors.append(args)
        self.app.attributes('-alpha', 0)
        self.app.deiconify()
        for language in ('Tiếng Việt', 'English'):
            self.app.change_language(language)
            for dimensions in ('1100x700', '1380x880'):
                self.app.geometry(dimensions)
                self.app.update()
                self.app.update_idletasks()
                right = self.app.winfo_rootx() + self.app.winfo_width()
                self.assertLessEqual(self.app.run_button.winfo_rootx() + self.app.run_button.winfo_width(), right)
                self.assertLessEqual(self.app.inspector.winfo_rootx() + self.app.inspector.winfo_width(), right)
                for row in self.app.rows.values():
                    self.assertLessEqual(row.description.winfo_rooty() + row.description.winfo_height(),
                                         row.winfo_rooty() + row.winfo_height())
        self.app.withdraw()
        self.assertEqual(errors, [])


class FilterTests(unittest.TestCase):
    def test_accent_normalization(self):
        self.assertEqual(normalize('Quyền riêng tư ĐÃ CHỌN'), 'quyen rieng tu da chon')
        self.assertEqual(category_for('disable-edge-telemetry.yaml'), 'privacy')
        self.assertEqual(category_for('disable-vbs.yaml'), 'protection')


if __name__ == '__main__':
    unittest.main()
