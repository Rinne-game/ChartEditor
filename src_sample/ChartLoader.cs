//this is samplecode for Unity.
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using System;
using System.Linq;
using System.Text.RegularExpressions;

public class ChartLoader : MonoBehaviour
{
    public static chartfile ImportChartFromText(string text)
    {
        chartfile chart = new chartfile
        {
            notes = new List<TimelineEvent>(),
            Gimmick = new List<GimickRow>()
        };

        int laneCount = 5;
        int currentLayer = 0;

        string[] lines = text.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);

        foreach (string rawLine in lines)
        {
            string line = rawLine.Trim();
            if (string.IsNullOrWhiteSpace(line)) continue;

            if (line.StartsWith("lane:"))
            {
                if (int.TryParse(line.Substring(5), out int lane)) laneCount = lane;
                continue;
            }
            else if (line.StartsWith("#layer:"))
            {
                if (int.TryParse(line.Substring(7), out int layer)) currentLayer = layer;
                Debug.Log($"Layer:{layer}({line})");
                continue;
            }

            string[] timeSplit = line.Split('|');
            if (timeSplit.Length < 2) continue;

            if (!float.TryParse(timeSplit[0], out float time)) continue;

            string[] noteSymbols = timeSplit[1].Split(',').Select(s => s.Trim()).ToArray();
            if (noteSymbols.Length != laneCount) continue;

            string extraData = timeSplit.Length >= 3 ? timeSplit[2] : "";
            Dictionary<int, float> holdLengths = new Dictionary<int, float>();

            // Hold Length
            if (extraData.Contains("Length:["))
            {
                int start = extraData.IndexOf("Length:[") + 8;
                int end = extraData.IndexOf("]", start);
                if (end > start)
                {
                    var values = extraData.Substring(start, end - start).Split(',');
                    for (int i = 0; i < values.Length && i < laneCount; i++)
                    {
                        if (float.TryParse(values[i], out float len))
                            holdLengths[i] = len;
                    }
                }
            }
            if (currentLayer >= 0)
            {
                Debug.Log($"Layer:{currentLayer}:>>{(extraData == "" ? "None" : extraData)}");
                // Debug.Log($"Layer:{currentLayer}Time:{time}TagData:{extraData}>>[G:Scroll=]:{extraData.Contains("G:Scroll=")},Speed:{extraData.Contains("Speed:[")}");
                // Scroll gimmick
                if (extraData.Contains("Scroll="))
                {
                    var match = Regex.Match(extraData, @"G:Scroll=([-+]?[0-9]*\.?[0-9]+)");
                    if (match.Success)
                    {
                        chart.Gimick.Add(new GimickRow
                        {
                            type = "Scroll",
                            time = time,
                            speed = float.Parse(match.Groups[1].Value),
                            Layer = Math.Max(0, currentLayer)
                        });
                        Debug.Log($"Layer:{currentLayer}>>G:Scroll,isSuccess:{match.Success}>>Code:{JsonUtility.ToJson(chart.Gimick[chart.Gimick.Count - 1])}");
                    }
                    else
                        Debug.Log($"Layer:{currentLayer}>>G:Scroll,isSuccess:{match.Success}");
                }
                // Speed gimmick (段階変化)
                if (extraData.Contains("Speed:["))
                {
                    var match = Regex.Match(extraData, @"Speed:\[(\d+\.\d+)~(\d+\.\d+)\]=(\d+\.\d+)\>(\d+\.\d+)");
                    if (match.Success)
                    {
                        chart.Gimick.Add(new GimickRow
                        {
                            type = "Speed",
                            time = float.Parse(match.Groups[1].Value),
                            time_end = float.Parse(match.Groups[2].Value),
                            speed_before = float.Parse(match.Groups[3].Value),
                            speed_after = float.Parse(match.Groups[4].Value),
                            Layer = Math.Max(0, currentLayer)
                        });
                    }
                }
            }

            // Notes
            for (int i = 0; i < noteSymbols.Length && i < laneCount; i++)
            {
                string tag = noteSymbols[i];
                if (tag == "-N") continue;

                EventAtt type = EventAtt.Tap;
                switch (tag)
                {
                    case "-T": type = EventAtt.Tap; break;
                    case "-F": type = EventAtt.Drag; break;
                    case "-D": type = EventAtt.Damage; break;
                    case "-H": type = EventAtt.Hold; break;
                    case "SL": type = EventAtt.SlideL; break;
                    case "SR": type = EventAtt.SlideR; break;
                    default: continue;
                }

                chart.notes.Add(new TimelineEvent
                {
                    time = time,
                    row = i,
                    eventType = type,
                    Length = holdLengths.ContainsKey(i) ? holdLengths[i] : 0f,
                    Layer = currentLayer
                });
            }
        }
        Debug.Log($"Total:notes:{chart.notes.Count},Gimmick:{chart.Gimick.Count}(Layer.Count:{chart.Gimick.Max(item => item.Layer) - chart.Gimick.Min(item => item.Layer) + 1}({chart.Gimick.Min(item => item.Layer)}~{chart.Gimick.Max(item => item.Layer)}))");
        return chart;
    }

}

[System.Serializable]
public class TimelineEvent
{
    public float time;
    public int row;
    public EventAtt eventType;
    public bool isDragging = false;
    public bool isPlayed = false; // 再生されたかどうか
                                  //ここからはホールドだけ
    public float Length = 1f;
    public EventAtt eventType_Start;
}

[System.Serializable]
public class GimickRow
{
    public string type;//
    public float time; // 時間
    public float time_end; //変化に時間がかかる系のギミックの終了時間
                           //--速度変化ギミック1("Scroll")--
    public float speed; // 新しい速度
    public float bpm;
    //--速度変化ギミック2("Speed")--
    public float speed_before;// 古い速度
    public float speed_after;// 新しい速度
    public string text;//表示させたいテキスト(0文字なら背景も非表示)
    public int Layer;//Layer>=0
}