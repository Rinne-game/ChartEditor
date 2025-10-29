from chart_editor_io import ChartEditor
from tkinter import filedialog, messagebox
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
import math
import pygame

class ChartEditor(ChartEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pygame ミキサー初期化
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error as e:
            print(f"[AUDIO] Pygame mixer init error: {e}")

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
            self.audio_path = path
            pygame.mixer.music.load(path)
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
    
    def play_audio(self):
        """音楽の再生／一時停止"""
        if not self.audio_path:
            messagebox.showwarning("警告", "音楽ファイルが読み込まれていません。")
            return
        if not self.is_playing:
            pygame.mixer.music.play()
            self.is_playing = True
            print("[AUDIO] ▶ 再生開始")
        else:
            pygame.mixer.music.pause()
            self.is_playing = False
            print("[AUDIO] ⏸ 一時停止")

    def stop_audio(self):
        """停止"""
        pygame.mixer.music.stop()
        self.is_playing = False
        print("[AUDIO] ⏹ 再生停止")

    def get_audio_position(self):
    #再生中の音楽の現在位置を秒単位で取得
    #再生していない場合は 0 を返す
        if not self.is_playing:
            return 0.0
        pos_ms = pygame.mixer.music.get_pos()  # ミリ秒単位
        bpm = self.bpm.get()  # chart_editor_base.py の self.bpm
        measures = (pos_ms / 1000.0) * bpm / 60 / 4
        return measures
    def drew_audio_play_line(self):
        self.canvas.delete("play_line")
        if  self.audio_path:
            x1 = ((-1+1)/2*self.canvas_width)+(self.canvas_width/2)
            x2 = ((1+1)/2*self.canvas_width)+(self.canvas_width/2)
            y=(self.get_audio_position()*-1)
            # y=(self.total_measures-self.get_audio_position())*self.measure_height
            y_max=self.total_measures*self.measure_height
            self.canvas.create_line(x1, y*self.measure_height, x2, y*self.measure_height,
                                        fill="red", width=4, tags="play_line")#, dash=(4,2)
        self.after(16, self.drew_audio_play_line)
