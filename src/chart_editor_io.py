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
        # ✅ lane= から lane: に修正
        lines.append(f"lane:{self.lane_count}")

        # ===== lane_move 出力 =====
        if include_lane_move:
            lines.append("##lane_move")
            for kf in self.lane_keyframes:
                pos_list = ",".join(f"{x:.4f}" for x in kf["posx"])
                lines.append(f"{kf['timing']}| [{pos_list}]")

        # ===== レイヤーブロック =====
        layers = sorted(set(note["layer"] for note in self.notes))
        for layer in layers:
            lines.append(f"#layer:{layer}")

            grouped = {}
            for note in self.notes:
                if note["layer"] != layer:
                    continue

                timing = note["measure"] + note["beat"] / 4.0
                if timing not in grouped:
                    grouped[timing] = ["-N"] * self.lane_count

                if note["type"] == "Tap":
                    grouped[timing][note["lane"]] = "-T"
                elif note["type"] == "Feel":
                    grouped[timing][note["lane"]] = "-F"
                elif note["type"] == "Slide-L":
                    grouped[timing][note["lane"]] = "SL"
                elif note["type"] == "Slide-R":
                    grouped[timing][note["lane"]] = "SR"
                elif note["type"] == "Hold":
                    grouped[timing][note["lane"]] = "-H"

            for timing in sorted(grouped.keys()):
                line = f"{timing:.3f}| {','.join(grouped[timing])} |"
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
        self.lane_count = 0
        current_layer = None
        mode = None

        lane_move_pattern = re.compile(r"([\d.]+)\s*\|\s*\[([0-9eE+,\-. ]+)\]")
        note_line_pattern = re.compile(r"([\d.]+)\s*\|\s*([^\|]*)\|")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # ✅ lane= → lane:
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

            if mode == "lane_move":
                m = lane_move_pattern.match(line)
                if m:
                    timing = float(m.group(1))
                    posx = [float(x) for x in m.group(2).split(",")]
                    self.lane_keyframes.append({"timing": timing, "posx": posx})
                continue

            if mode == "layer":
                m = note_line_pattern.match(line)
                if not m:
                    continue

                t = float(m.group(1))
                note_list = [n.strip() for n in m.group(2).split(",")]

                for i, mark in enumerate(note_list):
                    if mark == "-T": ntype = "Tap"
                    elif mark == "-F": ntype = "Feel"
                    elif mark == "SL": ntype = "Slide-L"
                    elif mark == "SR": ntype = "Slide-R"
                    elif mark == "-H": ntype = "Hold"
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
