import tkinter as tk
from tkinter import ttk, filedialog
import platform
import pygame

class ChartEditor(tk.Tk):
    def __init__(self):
        # chart_editor_base.py など
        APP_NAME = "TapLine 譜面エディター"
        APP_VERSION = "0.7.0"
        super().__init__()
        self.title(f"{APP_NAME} Ver.{APP_VERSION}")
        self.geometry("1000x700")

        self.bpm = tk.DoubleVar(value=120.0)
        self.lane_count = 6
        self.total_measures = 4
        self.measure_height = 400
        self.canvas_width = 360
        self.audio_path = None
        self.is_playing = False

        # 追加：スナップ設定
        self.snap_mode = tk.StringVar(value="なし")  # "なし" / "3分" / "4分" / "5分" / "6分"

        # プロモード用変数
        self.pro_mode_var = tk.BooleanVar(value=False)

        # メニューバー作成（Mac対応）
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        settings_File = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=settings_File)
        settings_File.add_command(label = "ファイルを開く",  accelerator="Ctrl+O")
        settings_File.add_command(label = "名前を付けて保存",  accelerator="Ctrl+S")
        settings_File.add_command(label = "音楽ファイルを選択")

        settings_Edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集", menu=settings_Edit)
        settings_Edit.add_command(label = "元に戻す")
        settings_Edit.add_command(label = "やり直し")

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="設定", menu=settings_menu)
        settings_menu.add_checkbutton(
            label="プロモード",
            variable=self.pro_mode_var,
            #command=self.on_pro_mode_toggle  # ← メソッドを呼ぶ
        )

        self.radio_val = tk.IntVar() # ラジオボタンの値
        settings_choose = tk.Menu(menubar, tearoff=0)
        settings_choose_Mode = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="選択", menu=settings_choose)
        settings_choose.add_cascade(label="モード", menu=settings_choose_Mode)
        settings_choose_Mode.add_radiobutton(label = "選択１",  variable = self.radio_val, value = 1)
        settings_choose_Mode.add_radiobutton(label = "選択２",  variable = self.radio_val, value = 2)
        settings_choose_Mode.add_radiobutton(label = "選択３",  variable = self.radio_val, value = 3)

        self.lane_positions = {
        i: [{"measure": 0, "x":i * 30+15}]  # 初期小節の位置だけ
        for i in range(self.lane_count)
        }# ((i * 30+15) / self.canvas_width) * 2 - 1 
        self.lane_keyframes = [{
                "timing": 0.0,  # 初期タイミング
                "posx": [(((i)/(self.lane_count)) * 2 - 1 + (1/(self.lane_count))) for i in range(self.lane_count)]
            }
        ]
            #{
            #    "timing": 16.0,  # 初期タイミング
            #    "posx": [(((i)/(self.lane_count)) * 2 - 1 + (1/(self.lane_count))) for i in range(self.lane_count)]
            #}
        # print(self.lane_keyframes)
        self.notes = []
        note_types = ["Tap", "Feel", "Slide-L", "Slide-R", "Hold"]
        self.note_type_var = tk.StringVar(value="Tap")

        self._build_ui()

    def _build_ui(self):
        # メニューバー作成
        os_name = platform.system()
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        settings_File = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=settings_File)
        settings_Edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集", menu=settings_Edit)
        if os_name == "Darwin":#Mac版はcommandになる
            settings_File.add_command(label = "ファイルを開く",command=self.load_tlc,  accelerator="Cmd+O")#,state="disabled"
            settings_File.add_command(label = "名前を付けて保存",command=self.save_tlc,  accelerator="Cmd+S")
            settings_File.add_separator() # ここに線が挿入される
            settings_File.add_command(label = "音楽ファイルを選択" ,command=self.load_audio)
            settings_Edit.add_command(label = "元に戻す",  accelerator="Cmd+Z",state="disabled")
            settings_Edit.add_command(label = "やり直し",  accelerator="Shift+Cmd+Z",state="disabled")
            self.bind("<Command-s>", self.save_tlc)
            self.bind("<Command-o>", self.load_tlc)
        else:
            settings_File.add_command(label = "ファイルを開く",command=self.load_tlc,  accelerator="Ctrl+O")
            settings_File.add_command(label = "名前を付けて保存",command=self.save_tlc,  accelerator="Ctrl+S")
            settings_File.add_separator() # ここに線が挿入される
            settings_File.add_command(label = "音楽ファイルを選択" ,command=self.load_audio)
            settings_Edit.add_command(label = "元に戻す",  accelerator="Ctrl+Z",state="disabled")
            settings_Edit.add_command(label = "やり直し",  accelerator="Shift+Ctrl+Z",state="disabled")
            self.bind("<Control-s>", self.save_tlc)
            self.bind("<Control-o>", self.load_tlc)

        # 「設定」メニュー
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="設定", menu=settings_menu)
        # self.pro_mode_var.get()
        # プロモードチェック
        self.pro_mode_var = tk.BooleanVar(value=False)
        settings_menu.add_checkbutton(
            label="Proモード",
            variable=self.pro_mode_var,
            #command=self.on_pro_mode_toggle
            #state="disabled"  # ← 無効化
        )

        self.mode = "note"  # 初期モード: ノーツ配置(N)
        top = ttk.Frame(self)

        top.pack(fill="x", pady=5)
        ttk.Label(top, text="BPM:").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=self.bpm, width=8).pack(side="left")
        # ttk.Button(top, text="音楽ファイルを選択", command=self.load_audio).pack(side="left", padx=10)

        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill="x", pady=5)


        self.radio_val = tk.IntVar() # ラジオボタンの値

        self.mode_var = tk.StringVar()
        settings_choose = tk.Menu(menubar, tearoff=0)
        settings_choose_Mode = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="選択", menu=settings_choose)
        settings_choose.add_cascade(label="モード", menu=settings_choose_Mode)#,state="disabled"
        settings_choose_Mode.add_radiobutton(label = "ノーツ配置",  accelerator="N", command = self.on_mode_change,  variable = self.mode_var, value = "ノーツ配置(N)")
        settings_choose_Mode.add_radiobutton(label = "レーン編集",  accelerator="L", command = self.on_mode_change, variable = self.mode_var, value = "レーン編集(L)")
        settings_choose_Mode.add_radiobutton(label = "選択/削除",  accelerator="S", command = self.on_mode_change, variable = self.mode_var, value = "選択/削除(S)")
        self.note_type_var = tk.StringVar(value="Tap")
        settings_choose_Notes = tk.Menu(menubar, tearoff=0)
        settings_choose.add_cascade(label="ノーツ", menu=settings_choose_Notes)#,state="disabled"
        settings_choose_Notes.add_radiobutton(label = "Tap",  accelerator="1",  variable = self.note_type_var, value = "Tap")
        settings_choose_Notes.add_radiobutton(label = "Feel",  accelerator="2",  variable = self.note_type_var, value = "Feel")
        settings_choose_Notes.add_radiobutton(label = "Slide-L",  accelerator="3",  variable = self.note_type_var, value = "Slide-L")
        settings_choose_Notes.add_radiobutton(label = "Slide-R",  accelerator="4",  variable = self.note_type_var, value = "Slide-R")
        settings_choose_Notes.add_radiobutton(label = "Hold",  accelerator="5",  variable = self.note_type_var, value = "Hold",state="disabled")
        # note_types = ["Tap", "Feel", "Slide-L", "Slide-R", "Hold"]
        self.mode_var.set("ノーツ配置(N)")  # 初期値
        # if self.pro_mode_var.get() else"ノーツ配置"
        self.mode_dropdown = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["ノーツ配置(N)", "レーン編集(L)", "選択/削除(S)"],# """if self.pro_mode_var.get() else["ノーツ配置", "レーン編集", "選択/削除"]"""
            # state="readonly",
            width=12,
            state="disabled"
        )
        self.mode_dropdown.pack(side="left")
        snap_frame = ttk.Frame(self)
        snap_frame.pack(fill="x", pady=3)
        self.snap_mode.set("4分")  # 初期値
        ttk.Label(snap_frame, text="自動補正:").pack(side="left", padx=5)
        snap_combo = ttk.Combobox(
            snap_frame,
            textvariable=self.snap_mode,
            values= ["なし", "3分", "4分", "5分", "6分"],#, "カスタム"
            state="readonly",
            width=8
        )
        snap_combo.pack(side="left", padx=3)

        # _build_ui の下部（snap_frameの下あたり）に追加
        layer_frame = ttk.Frame(self)
        layer_frame.pack(fill="x", pady=3)

        ttk.Label(layer_frame, text="レイヤー:").pack(side="left", padx=5)
        self.layer_var = tk.IntVar(value=0)

        layer_spin = ttk.Spinbox(layer_frame, from_=-10, to=10, textvariable=self.layer_var, width=5, state="disabled")
        layer_spin.pack(side="left", padx=3)
        # snap_combo.bind("<<ComboboxSelected>>", on_snap_change)

        # ▼ 準備工事：カスタム入力用（今は機能しない）
        self.custom_snap = tk.StringVar(value="")
        snap_entry = ttk.Entry(snap_frame, textvariable=self.custom_snap, width=6, state="disabled")
        snap_entry.pack(side="left", padx=3)
        self.mode_dropdown.bind("<<ComboboxSelected>>", self.on_mode_change)

        #self.mode_label = ttk.Label(mode_frame, text=f"現在のモード: {self.mode}")
        #self.mode_label.pack(side="left", padx=10)


        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame, bg="black")
        self.v_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scroll.pack(side="right", fill="y")
        self.label_tips = ttk.Label(layer_frame,text=f"一部を除くショートカットキーは、Proモードを有効にすると使用可能となります。")
        self.label_tips.pack(side="left", padx=3)

        self.dragging_lane = None

        bottom = ttk.Frame(self)
        bottom.pack(fill="x")
        # 左側にクレジット表示
        credit_label = ttk.Label(bottom, text="Built with Tkinter in Python", foreground="gray70")
        credit_label.pack(side="left", padx=5)

        # タイムライン表示
        self.timeline_label = ttk.Label(bottom, text=f"タイムライン（表示小節 0 - {self.total_measures}）")
        self.timeline_label.pack(side="left", padx=10)

        # self.canvas.bind("<Button-1>", self.on_canvas_click)
        # if self.pro_mode_var.get():
        self.bind("n", lambda e: self.set_mode("note",True))
        self.bind("l", lambda e: self.set_mode("lane",True))
        self.bind("s", lambda e: self.set_mode("select",True))
        self.bind("<space>", lambda e: self.play_audio())
        # self.bind("s", lambda e: self.stop_audio)
        self.bind("1", lambda e: self.set_note_type("Tap"))
        self.bind("2", lambda e: self.set_note_type("Feel"))
        self.bind("3", lambda e: self.set_note_type("Slide-L"))#self.set_note_type("Slide-L")
        self.bind("4", lambda e: self.set_note_type("Slide-R"))#self.set_note_type("Slide-R")
        # note_types = ["Tap", "Feel", "Slide-L", "Slide-R", "Hold"]
            #self.set_note_type("Tap")
            # self.bind("5", lambda e: self.note_type_var = "Tap")
        # self.canvas.bind("<MouseWheel>", self.on_scroll)


        self._update_scrollregion()
        self.draw_grid()
        self.draw_lanes()#current_measure=0
        self.draw_notes()
        self.bind_scroll_events()
        self.drew_audio_play_line()


    def on_mode_change(self, event=None):
        mode_text = self.mode_var.get()
        if mode_text == "ノーツ配置(N)":
            self.set_mode("note",False)
        elif mode_text == "レーン編集(L)":
            self.set_mode("lane",False)
        elif mode_text == "選択/削除(S)":
            self.set_mode("select",False)

    def set_mode(self, mode,isshortcut):
        #if self.pro_mode_var.get() != True:
        if isshortcut and self.pro_mode_var.get() != True:
           return
        self.mode = mode
        # print("called")
        # ドロップダウンも同期
        if mode == "note":
            self.mode_var.set("ノーツ配置(N)")
        elif mode == "lane":
            self.mode_var.set("レーン編集(L)")
        elif mode == "select":
            self.mode_var.set("選択/削除(S)")
        print(f"{self.mode}")#self.mode_var.set
        self.update_bindings()


    def update_bindings(self):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonPress-3>")
        self.canvas.unbind("<B3-Motion>")
        self.canvas.unbind("<ButtonRelease-3>")
        self.canvas.unbind("<Button-3>")

        if self.mode == "note":
            self.canvas.bind("<Button-1>", self.on_canvas_click)
        elif self.mode == "lane":
            self.canvas.bind("<ButtonPress-3>", self.start_lane_drag)
            self.canvas.bind("<B3-Motion>", self.drag_lane)
            self.canvas.bind("<ButtonRelease-3>", self.end_lane_drag)
            self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # 右クリックでレーン追加
        elif self.mode == "select":
            self.canvas.bind("<Shift-Button-1>", self.on_canvas_click_D)
    # 選択モードは後で拡張可
    def bind_scroll_events(self):
        """マウスホイール・ドラッグによるスクロール制御を設定"""
        # ホイールスクロール
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        # Mac対応（イベント名が異なる）
        # self.canvas.bind_all("<Button-4>", self.on_mouse_wheel_mac)
        # self.canvas.bind_all("<Button-5>", self.on_mouse_wheel_mac)

        # 中クリックによるドラッグスクロール
        #self.canvas.bind("<ButtonPress-2>", self.start_drag_scroll)
        #self.canvas.bind("<B2-Motion>", self.do_drag_scroll)
        #self.canvas.bind("<ButtonRelease-2>", self.end_drag_scroll)
        # os_name = platform.system()

    def on_mouse_wheel(self, event):
        os_name = platform.system()
        # if os_name != "Windows":
        #    return
        """Windows/Linux用ホイールスクロール"""
        delta = int(-event.delta / 2)
        self.canvas.yview_scroll(delta, "units")
        # self.redraw_all()

    def on_mouse_wheel_mac(self, event):
        os_name = platform.system()
        # if os_name != "Darwin":
        #    return
        """Mac用ホイールスクロール"""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        # self.redraw_all()

    def start_drag_scroll(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_drag_scroll(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        # self.canvas.scan_dragto(self.canvas.scan_mark_x, event.y, gain=1)

    def end_drag_scroll(self, event):
        pass  # 将来的に慣性なども追加可
    
    def redraw_all(self):
        self.draw_grid()
        self.draw_lanes()#current_measure=0
        self.draw_notes()

    def set_note_type(self,Ntype):
        print(Ntype)
        if self.pro_mode_var.get()!=True:
            return
        # self.note_type_var=Ntype
        #self.mode_var.set("ノーツ配置(N)")
        self.note_type_var.set(Ntype)