from chart_editor_notes import ChartEditor
from tkinter import filedialog, messagebox
import re
import os

class ChartEditor(ChartEditor):

    # ===============================
    # 📤 保存 (.tlc / .rgc)
    # ===============================
    def save_tlc(self, event=None):
        path = filedialog.asksaveasfilename(
            title="譜面ファイルを保存",
            defaultextension=".tlc",
            filetypes=[("TapLineChart", "*.tlc"), ("RythmGame Chart", "*.rgc")]
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        include_lane_move = (ext == ".tlc")

        lines = []
        lines.append(f"lane:{self.lane_count}")

        # ===== レーン移動 =====
        if include_lane_move:
            lines.append("##lane_move")
            for kf in self.lane_keyframes:
                pos_list = ",".join(f"{x:.4f}" for x in kf["posx"])
                lines.append(f"{kf['timing']} | [{pos_list}]")

        # ===== ノーツ =====
        layers = sorted(set(note["layer"] for note in self.notes))
        for layer in layers:
            lines.append(f"#layer:{layer}")
            timings = set()
            # ノーツ由来
            for note in self.notes:
                if note["layer"] == layer:
                    timings.add(note["measure"] + note["beat"]/4)

            if not hasattr(self, 'timing_extras'):
                self.timing_extras = {}
            # ギミック由来
            for t in self.timing_extras.keys():
                timings.add(t)
            
            grouped = {}

            for timing in sorted(timings):
                grouped[timing] = {
                "notes": ["-N"] * self.lane_count,
                "extra": self.timing_extras.get(timing, "")
            }
            for note in self.notes:
                if note["layer"] != layer:
                    continue

                timing = round(note["measure"] + note["beat"]/4, 3)

                lane = note["lane"]
                ntype = note["type"]
                if ntype == "Tap":
                    grouped[timing]["notes"][lane] = "-T"
                elif ntype == "Feel":
                    grouped[timing]["notes"][lane] = "-F"
                elif ntype == "Slide-L":
                    grouped[timing]["notes"][lane] = "SL"
                elif ntype == "Slide-R":
                    grouped[timing]["notes"][lane] = "SR"
                elif ntype == "Hold":
                    grouped[timing]["notes"][lane] = "-H"

            for timing in sorted(grouped.keys()):
                notes = ",".join(grouped[timing]["notes"])
                extra = grouped[timing]["extra"]
                line = f"{timing:.3f} | {notes} | {extra}"
                lines.append(line)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("保存完了", f"{path} に保存しました。")
        except Exception as e:
            messagebox.showerror("保存失敗", str(e))


    # ===============================
    # 📥 読み込み (.tlc / .rgc)
    # ===============================
    def load_tlc(self, event=None):
        path = filedialog.askopenfilename(
            title="譜面ファイルを読み込み",
            filetypes=[("TapLineChart/RythmGame Chart", "*.tlc *.rgc")]
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        include_lane_move = (ext == ".tlc")

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.lane_keyframes = []
        self.notes = []
        self.timing_extras = {}   # ★追加：ギミック保持用
        self.lane_count = 0

        current_layer = None
        mode = None

        lane_move_pattern = re.compile(r"([\d.]+)\s*\|\s*\[([0-9eE+,\-. ]+)\]")
        note_line_pattern = re.compile(r"([\d.]+)\s*\|\s*([^|]*)\|\s*(.*)")

        for raw in lines:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("lane:"):
                self.lane_count = int(line.split(":")[1])
                continue

            elif line.startswith("#layer:"):
                current_layer = int(line.split(":")[1])
                mode = "layer"
                continue

            elif line.startswith("##lane_move") and include_lane_move:
                mode = "lane_move"
                continue

            elif line.startswith("##"):
                mode = None
                continue

            # ===== lane_move =====
            if mode == "lane_move":
                m = lane_move_pattern.match(line)
                if m:
                    timing = float(m.group(1))
                    posx = [float(x) for x in m.group(2).split(",")]
                    self.lane_keyframes.append({"timing": timing, "posx": posx})
                continue

            # ===== ノーツ =====
            if mode == "layer":
                m = note_line_pattern.match(line)
                if not m:
                    continue

                timing = float(m.group(1))
                note_list = [n.strip() for n in m.group(2).split(",")]
                extra = m.group(3).strip()

                # ★ extraData を timing 単位で保存
                if extra:
                    self.timing_extras[timing] = extra

                for i, mark in enumerate(note_list):
                    if mark == "-N":
                        continue

                    if mark == "-T":
                        ntype = "Tap"
                    elif mark == "-F":
                        ntype = "Feel"
                    elif mark == "SL":
                        ntype = "Slide-L"
                    elif mark == "SR":
                        ntype = "Slide-R"
                    elif mark == "-H":
                        ntype = "Hold"
                    else:
                        continue

                    self.notes.append({
                        "measure": timing,
                        "beat": 0.0,
                        "lane": i,
                        "type": ntype,
                        "layer": current_layer
                    })

        # ===== lane_move 無い場合の初期化 =====
        if not include_lane_move and self.lane_count > 0:
            self.lane_keyframes.append({
                "timing": 0.0,
                "posx": [((i / self.lane_count) * 2 - 1 + (1 / self.lane_count))
                         for i in range(self.lane_count)]
            })

        self.redraw_all()
        messagebox.showinfo("読み込み完了", f"{path} を読み込みました。")
