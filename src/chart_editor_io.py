from chart_editor_notes import ChartEditor
from tkinter import filedialog, messagebox
import re

class ChartEditor(ChartEditor):

    # ===============================
    # 📤 保存 (.tlc)
    # ===============================
    def save_tlc(self):
        path = filedialog.asksaveasfilename(
            title="譜面ファイルを保存",
            defaultextension=".tlc",
            filetypes=[("TapLineChart", "*.tlc"), ("RythmGame Chart", "*.rgc")]
        )
        if not path:
            return
        
        # 出力形式を拡張子で判断
        ext = os.path.splitext(path)[1].lower()
        include_lane_move = (ext == ".tlc")

        lines = []
        lines.append(f"lane={self.lane_count}")  # lane行

        # ===== レーン位置ブロック =====
        if include_lane_move:
            lines.append("##lane_move")
            for kf in self.lane_keyframes:
                pos_list = ",".join(f"{x:.4f}" for x in kf["posx"])
                lines.append(f"{kf['timing']} | [{pos_list}]")

        # ===== ノーツブロック =====
        layers = sorted(set(note["layer"] for note in self.notes))
        for layer in layers:
            lines.append(f"#layer:{layer}")
            layer_notes = [n for n in self.notes if n["layer"] == layer]
            for n in sorted(layer_notes, key=lambda x: (x["measure"], x["beat"])):
                t = n["measure"] + n["beat"] / 4
                #note_types = ["Tap", "Feel", "Slide-L", "Slide-R", "Hold"]
                # ノーツ種別変換
                note_type = n["type"]
                if note_type == "Tap":
                    mark = "-T"
                elif note_type == "Feel":
                    mark = "-F"
                elif note_type == "Slide-L":
                    mark = "SL"
                elif note_type == "Slide-R":
                    mark = "SR"
                else:
                    mark = "-N"

                # lane に応じて配置
                notes_row = ["-N"] * self.lane_count
                notes_row[n["lane"]] = mark
                notes_text = ",".join(notes_row)

                lines.append(f"{t:.3f} | {notes_text} |")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("保存完了", f"{path} に保存しました。")
        except Exception as e:
            messagebox.showerror("保存失敗", str(e))


    # ===============================
    # 📥 読み込み (.tlc)
    # ===============================
    def load_tlc(self):
        path = filedialog.askopenfilename(
            title="譜面ファイルを読み込み",
            filetypes=[("TapLineChart/RythmGame Chart", "*.tlc *.rgc")]
        )
        #("音楽ファイル", "*.mp3 *.ogg"),  # oggは将来的に有効化
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        include_lane_move = (ext == ".tlc")

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.lane_keyframes = []
        self.notes = []
        self.lane_count = 0
        current_layer = None
        mode = None

        lane_move_pattern = re.compile(r"([\d.]+)\s*\|\s*\[([0-9eE+,\-. ]+)\]")
        note_line_pattern = re.compile(r"([\d.]+)\s*\|\s*([^\|]*)\|")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("lane="):
                self.lane_count = int(line.split("=")[1])
                continue

            elif line.startswith("#layer:"):
                current_layer = int(line.split(":")[1])
                mode = "layer"
                continue

            elif line.startswith("##lane_move") and include_lane_move:
                mode = "lane_move"
                continue

            elif line.startswith("##"):
                mode = None  # 将来対応予定ブロック
                continue

            # ===== lane_moveブロック =====
            if mode == "lane_move":
                m = lane_move_pattern.match(line)
                if m:
                    timing = float(m.group(1))
                    posx = [float(x) for x in m.group(2).split(",")]
                    self.lane_keyframes.append({"timing": timing, "posx": posx})
                continue

            # ===== layerブロック =====
            if mode == "layer":
                m = note_line_pattern.match(line)
                if not m:
                    continue
                t = float(m.group(1))
                note_list = [n.strip() for n in m.group(2).split(",")]

                #note_types = ["Tap", "Feel", "Slide-L", "Slide-R", "Hold"]
                for i, mark in enumerate(note_list):
                    if mark == "-N":
                        continue
                    elif mark == "-T":
                        ntype = "Tap"
                    elif mark == "-F":
                        ntype = "Feel"
                    elif mark == "SL":
                        ntype = "Slide-L"
                    elif mark == "SR":
                        ntype = "Slide-R"
                    else:
                        continue

                    self.notes.append({
                        "measure": t,
                        "beat": 0.0,
                        "lane": i,
                        "type": ntype,
                        "layer": current_layer
                    })

        self.redraw_all()
        messagebox.showinfo("読み込み完了", f"{path} を読み込みました。")
