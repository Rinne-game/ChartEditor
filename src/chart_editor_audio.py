from chart_editor_io import ChartEditor
from tkinter import filedialog, messagebox
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
import math

class ChartEditor(ChartEditor):

    def load_audio(self):
        print("loaded")
        """音楽ファイルを読み込み、曲の長さとBPMから小節数を自動算出"""
        path = filedialog.askopenfilename(
            title="音楽ファイルを選択",
            filetypes=[
                ("音楽ファイル", "*.mp3 *.ogg"),  # oggは将来的に有効化
                ("MP3 ファイル", "*.mp3"),
                ("OGG ファイル", "*.ogg"),
            ]
        )
        print("loaded")
        if not path:
            # messagebox.showerror("エラー", f"ダイアログの表示に失敗しました")
            return

        try:
            if path.lower().endswith(".mp3"):
                audio = MP3(path)
            elif path.lower().endswith(".ogg"):
                audio = OggVorbis(path)
            else:
                raise ValueError("対応形式はmp3/oggのみです。")

            duration_sec = audio.info.length  # 秒単位
            bpm = self.bpm.get()  # chart_editor_base.py の self.bpm
            self.total_measures = math.ceil(duration_sec * bpm / 60 / 4)
            print(f"曲の長さ: {duration_sec:.2f}秒, total_measures: {self.total_measures}")

            self._update_scrollregion()
            self.redraw_all()
        except Exception as e:
            messagebox.showerror("エラー", f"音楽ファイルの読み込みに失敗しました\n{e}")