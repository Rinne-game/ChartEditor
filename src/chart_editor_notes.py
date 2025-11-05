from chart_editor_lanes import ChartEditor
import math

class ChartEditor(ChartEditor):
    def on_canvas_click(self, event):
        # Canvas 内部座標に変換（スクロール対応）
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # 上昇スクロールでは y が負方向に増えるため反転して小節位置を得る
        measure_float = -cy / self.measure_height

        # === 小節・拍計算 ===
        bpm_beats = getattr(self, "beats_per_measure", 4)
        measure_index = math.floor(measure_float)
        beat_fraction = (measure_float - measure_index) * bpm_beats

        # === 🔧 スナップ補正 ===
        mode = self.snap_mode.get()
        snap_div = {
            "3分": 3,
            "4分": 4,
            "5分": 5,
            "6分": 6,
        }.get(mode, None)

        if snap_div:
            snap_unit = 1 / snap_div
            beat_fraction = round(beat_fraction / snap_unit) * snap_unit

        # === レーン推定 ===
        lane_id = self.get_nearest_lane(cx, measure_float)
        lane_x = self.interpolate_lane_x(lane_id, measure_float)
        layer = self.layer_var.get()

        # === ノーツ作成 ===
        note = {
            "measure": float(measure_index),
            "beat": float(beat_fraction),
            "lane": int(lane_id),
            "type": self.note_type_var.get(),
            "layer": layer,
        }
        replaced = False
        for i, existing in enumerate(self.notes):
            if (
                existing["lane"] == note["lane"] and
                abs(existing["measure"] - note["measure"]) < 1e-6 and
                abs(existing["beat"] - note["beat"]) < 1e-6 and
                existing["layer"] == note["layer"]
            ):
                self.notes[i] = note  # ← 上書き
                replaced = True
                print(f"Note replaced: {note}")
                break

        if not replaced:
            self.notes.append(note)
            print(f"Note added: {note}")

        # 再描画（新ノーツだけを描画してもOK）
        self.draw_notes()
    def on_canvas_click_D(self, event):
        # Canvas 内部座標に変換（スクロール対応）
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # 上昇スクロールでは y が負方向に増えるため反転して小節位置を得る
        measure_float = -cy / self.measure_height

        # === 小節・拍計算 ===
        bpm_beats = getattr(self, "beats_per_measure", 4)
        measure_index = math.floor(measure_float)
        beat_fraction = (measure_float - measure_index) * bpm_beats

        # === 🔧 スナップ補正 ===
        mode = self.snap_mode.get()
        snap_div = {
            "3分": 3,
            "4分": 4,
            "5分": 5,
            "6分": 6,
        }.get(mode, None)

        if snap_div:
            snap_unit = 1 / snap_div
            beat_fraction = round(beat_fraction / snap_unit) * snap_unit

        # === レーン推定 ===
        lane_id = self.get_nearest_lane(cx, measure_float)
        layer = self.layer_var.get()

        # === 右クリック時（削除） ===
        removed = False
        for i, existing in enumerate(self.notes):
            if (
                existing["lane"] == lane_id
                and abs(existing["measure"] - measure_index) < 1e-6
                and abs(existing["beat"] - beat_fraction) < 1e-6
                and existing["layer"] == layer
            ):
                del self.notes[i]
                removed = True
                print(f"Note deleted: lane={lane_id}, measure={measure_index}, beat={beat_fraction}")
                break

        if removed:
            self.draw_notes()


    def get_nearest_lane(self, x, measure_float):
        """クリック座標に最も近いレーンIDを返す"""
        min_dist = float("inf")
        nearest = 0
        for lane_id in range(self.lane_count):
            # lane_x はキャンバス座標へ変換
            lane_norm = self.interpolate_lane_x(lane_id, measure_float)
            lane_x = ((lane_norm + 1) / 2) * (540 - 180) + 180
            dist = abs(x - lane_x)
            if dist < min_dist:
                min_dist = dist
                nearest = lane_id
        return nearest


    def draw_note(self, note):
        layer = self.layer_var.get()
        if abs(note["layer"]) != layer:
            return

        # lane_x = self.interpolate_lane_x(note["lane"], note["measure"])
        lane_norm = self.interpolate_lane_x(note["lane"], note["measure"])
        lane_x = ((lane_norm + 1) / 2) * (540 - 180) + 180
        y = -(note["measure"] * self.measure_height + (note["beat"] / 4) * self.measure_height)
        x_limit = ((1/2*self.canvas_width)+(self.canvas_width/2))/12
        note_type = note.get("type", "Tap")
        size = 10

        if note_type == "Tap" or note_type == "Feel":
            self.canvas.create_rectangle(
                (lane_x - x_limit), (y - (size * 0.3)), (lane_x + x_limit), (y + (size * 0.3)),
                fill="white", outline="", tags="note"
            )

        # 色と形の選択
        if note_type == "Tap":
            color = "cyan"
            self.canvas.create_rectangle(
                (lane_x - x_limit)+1, (y - (size * 0.3))+1, (lane_x + x_limit)-1, (y + (size * 0.3))-1,
                fill=color, outline="", tags="note"
            )
            self.canvas.create_rectangle(
                (lane_x - (x_limit+1)/2), (y - ((size * 0.3)-1)/2), (lane_x + (x_limit-1)/2), (y + ((size * 0.3)-1)/2),
                fill="white", outline="", tags="note"
            )

        elif note_type == "Feel":
            color = "yellow"
            self.canvas.create_rectangle(
                (lane_x - x_limit)+1, (y - (size * 0.3))+1, (lane_x + x_limit)-1, (y + (size * 0.3))-1,
                fill=color, outline="", tags="note"
            )

        elif note_type == "Slide-L":
            color = "#3399FF"
            points = [
                lane_x - size, y,
                lane_x + size, y - size * 0.6,
                lane_x + size, y + size * 0.6
            ]
            self.canvas.create_polygon(points, fill=color, outline="", tags="note")

        elif note_type == "Slide-R":
            color = "#FF6666"
            points = [
                lane_x + size, y,
                lane_x - size, y - size * 0.6,
                lane_x - size, y + size * 0.6
            ]
            self.canvas.create_polygon(points, fill=color, outline="", tags="note")

        elif note_type == "Hold":
            color = "#00CC66"
            # Hold は準備中 → 半透明の印
            self.canvas.create_rectangle(
                lane_x - size, y - (size * 0.3), lane_x + size, y + (size * 0.3),
                outline=color, width=2, dash=(3, 3), tags="note"
            )


    def draw_notes(self):
        """全ノーツを再描画"""
        self.canvas.delete("note")
        for note in self.notes:
            self.draw_note(note)
