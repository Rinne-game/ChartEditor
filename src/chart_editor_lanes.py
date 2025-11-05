from chart_editor_base import ChartEditor

class ChartEditor(ChartEditor):
    def on_canvas_click_Lane(self, event):
        # レーン編集モードでなければ無視
        if self.mode_var.get() != "lane_edit":
            return

        # Shift 押下中のみ有効
        if not (event.state & 0x0001):  # Shift キーが押されていない
            return

        # Canvas 内座標に変換
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # 小節タイミング（上昇方向に合わせて反転）
        measure_float = -cy / self.measure_height

        # クリック位置からレーンIDを特定
        lane_id = self.get_nearest_lane(cx, measure_float)
        if lane_id is None:
            return

        # クリック位置の posx を正規化（-1.0〜1.0）
        posx = (cx - 180) / (540 - 180) * 2 - 1
        posx = max(-1.0, min(1.0, posx))  # TapLimit 内に制限

        print(f"[LaneEdit] Shift+Click: lane={lane_id}, timing={measure_float:.2f}, posx={posx:.2f}")

        # === 既存 keyframe の間に挿入 ===
        inserted = False
        for i in range(len(self.lane_keyframes) - 1):
            t1 = self.lane_keyframes[i]["timing"]
            t2 = self.lane_keyframes[i + 1]["timing"]
            if t1 <= measure_float <= t2:
                # posx 配列を複製して新しいタイミングを挿入
                new_posx = self.lane_keyframes[i]["posx"].copy()
                new_posx[lane_id] = posx
                self.lane_keyframes.insert(i + 1, {
                    "timing": measure_float,
                    "posx": new_posx
                })
                inserted = True
                break

        # 範囲外の場合は末尾に追加
        if not inserted:
            new_posx = self.lane_keyframes[-1]["posx"].copy()
            new_posx[lane_id] = posx
            self.lane_keyframes.append({
                "timing": measure_float,
                "posx": new_posx
            })

        # 再描画
        self.draw_lanes()

    def _update_scrollregion(self):
        total_height = self.total_measures * self.measure_height
        self.canvas.config(scrollregion=(0, -total_height, self.canvas_width, 0))
        self.timeline_label.config(
            text=f"タイムライン（表示小節 1 - {self.total_measures}）"
        )

    def draw_grid(self):
        self.canvas.delete("grid")
        for m in range(self.total_measures + 1):
            y = -m * self.measure_height
            is_strong = (m % 4 == 0)
            color = "gray80" if is_strong else "gray50"
            width = 2 if is_strong else 1
            self.canvas.create_line(self.canvas_width/2, y, self.canvas_width*3/2, y, fill=color, width=width, tags="grid")
            if m < self.total_measures:
                text_color = "white" if not is_strong else "#A0D8FF"
                self.canvas.create_text(-25+self.canvas_width/2, y-5, text=str(m),
                                        fill=text_color, font=("Arial", 12, "bold"), anchor="s", tags="grid")
        for m in range(self.total_measures):
            for beat in range(1,4):
                y = -(m*self.measure_height + self.measure_height/4*beat)
                self.canvas.create_line(self.canvas_width/2, y, self.canvas_width*3/2, y, fill="gray30", width=1, tags="grid")

    def draw_lanes(self):
        """上昇方向 + ドラッグ可能レーン表示"""
        self.canvas.delete("lane_line", "lane_handle", "lane_text")
        for i in range(self.lane_count):
            for j in range(len(self.lane_keyframes)):
                # print(f"[{i},{j}]")
                kf1 = self.lane_keyframes[j]

                # 通常区間: 次のキーフレームがある
                if j + 1 < len(self.lane_keyframes):
                    kf2 = self.lane_keyframes[j + 1]
                    x2 = ((kf2['posx'][i] + 1) / 2) * (540 - 180) + 180
                    y2 = -kf2['timing'] * self.measure_height
                else:
                    # 最後の要素: 次がないので total_measures まで伸ばす
                    x2 = ((kf1['posx'][i] + 1) / 2) * (540 - 180) + 180
                    y2 = -self.total_measures * self.measure_height

                # 始点
                x1 = ((kf1['posx'][i] + 1) / 2) * (540 - 180) + 180
                y1 = -kf1['timing'] * self.measure_height

                # 同一タイミングのときはスキップ（線分なし）
                if y1 == y2:
                    continue
                self.canvas.create_line(x1, y1, x2, y2, fill="gray70", tags="lane_line")
                size = 5
                self.canvas.create_oval(x1-size, y1-size, x1+size, y1+size, fill="cyan",
                                        tags=("lane_handle", f"lane_{i}"))
                self.canvas.create_text(x1, y1-15, text=f"{kf1['posx'][i]:.2f}",
                                        fill="white", font=("Arial",10), tags="lane_text", anchor="w")
        # TapLimitライン
        for limit in [-1.0,1.0]:
            x = ((limit+1)/2*self.canvas_width)+(self.canvas_width/2)
            self.canvas.create_line(x, -self.total_measures*self.measure_height, x, 0,
                                    fill="blue", width=2, dash=(4,2), tags="tap_limit")

    def interpolate_lane_x(self, lane_id, measure):
        """lane_id と timing から X座標を補間"""
        kfs = self.lane_keyframes
        if measure <= kfs[0]["timing"]:
            return kfs[0]["posx"][lane_id]
        if measure >= kfs[-1]["timing"]:
            return kfs[-1]["posx"][lane_id]
        for i in range(len(kfs)-1):
            t1, t2 = kfs[i]["timing"], kfs[i+1]["timing"]
            if t1 <= measure <= t2:
                x1, x2 = kfs[i]["posx"][lane_id], kfs[i+1]["posx"][lane_id]
                ratio = (measure - t1)/(t2 - t1)
                return x1 + (x2 - x1)*ratio

    def start_lane_drag(self, event):
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("lane_"):
                    lane_id = int(tag.split("_")[1])
                    # 最も近い keyframe を探す
                    nearest = min(self.lane_keyframes, key=lambda k: abs(self._keyframe_to_x(k, lane_id)-event.x))
                    self.dragging_lane = (lane_id, nearest)
                    return

    def drag_lane(self, event):
        if not self.dragging_lane:
            return
        lane_id, kf = self.dragging_lane
        coord = (event.x / self.canvas_width)*2-1
        coord = max(-1.0, min(1.0, coord))
        kf['posx'][lane_id] = coord
        self.draw_lanes()

    def end_lane_drag(self, event):
        self.dragging_lane = None

    def on_scroll(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)),"units")
        self.redraw_all()

    def add_lane_at_measure(self, measure, posx_list):
        """任意タイミングに新規レーン追加"""
        new_id = self.lane_count
        self.lane_count += 1
        # 全 keyframe に posx を追加
        for i, kf in enumerate(self.lane_keyframes):
            if i==0:
                kf['posx'].append(posx_list[i] if i<len(posx_list) else 0.0)
            else:
                kf['posx'].append(kf['posx'][-1])
        self.draw_lanes()

    def on_canvas_right_click(self, event):
        """右クリックでレーン追加"""
        measure = -event.y/self.measure_height
        x_norm = ((event.x-180)/(540-180))*2-1  # canvas->-1~1
        self.add_lane_at_measure(measure,[x_norm for _ in range(self.lane_count)])
