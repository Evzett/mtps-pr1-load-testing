"""Анализ результатов Artillery: сводные метрики и графики по каждому профилю нагрузки.

Запуск: python analyze.py  (читает results/p*.json, пишет results/summary.json и results/charts/*.png)
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
RES = HERE / "results"
CHARTS = RES / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

PROFILES = {
    "p1_smooth": "П1 «Плавный»",
    "p2_fast": "П2 «Быстрый»",
    "p3_spike": "П3 «Пиковый»",
    "p4_steps": "П4 «Ступенчатый»",
}
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 11})


def load(name):
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def timeline(data):
    """Ряды по 10-секундным интервалам: время от начала, RPS, p50/p95/p99, ошибки."""
    inter = sorted(data["intermediate"], key=lambda x: int(x["period"]))
    t0 = int(inter[0]["period"])
    rows = []
    for it in inter:
        c, s = it["counters"], it["summaries"].get("http.response_time", {})
        rows.append({
            "t": (int(it["period"]) - t0) / 1000,
            "rps": c.get("http.requests", 0) / 10,
            "p50": s.get("p50"), "p95": s.get("p95"), "p99": s.get("p99"),
            "errors": sum(v for k, v in c.items() if k.startswith("errors.")) + c.get("vusers.failed", 0) * 0,
            "vusers": c.get("vusers.created", 0) / 10,
        })
    return rows


def summarize(name, data):
    a = data["aggregate"]
    c, rt = a["counters"], a["summaries"]["http.response_time"]
    tl = timeline(data)
    errors = sum(v for k, v in c.items() if k.startswith("errors."))
    codes = {k.split(".")[-1]: v for k, v in c.items() if k.startswith("http.codes.")}
    duration = (a["lastMetricAt"] - a["firstMetricAt"]) / 1000
    endpoints = {
        k.split("response_time.", 1)[1]: {m: v[m] for m in ("median", "p95", "p99", "max")}
        for k, v in a["summaries"].items() if k.startswith("plugins.metrics-by-endpoint.response_time.")
    }
    return {
        "profile": PROFILES[name],
        "duration_s": round(duration),
        "vusers_created": c.get("vusers.created", 0),
        "vusers_completed": c.get("vusers.completed", 0),
        "vusers_failed": c.get("vusers.failed", 0),
        "requests": c.get("http.requests", 0),
        "responses": c.get("http.responses", 0),
        "codes": codes,
        "errors": errors,
        "error_rate_pct": round(100 * errors / max(c.get("http.requests", 1), 1), 2),
        "avg_rps": round(c.get("http.requests", 0) / duration, 1),
        "peak_rps": max(r["rps"] for r in tl),
        "rt": {k: rt[k] for k in ("min", "mean", "median", "p90", "p95", "p99", "max")},
        "downloaded_mb": round(c.get("http.downloaded_bytes", 0) / 1e6, 1),
        "endpoints": endpoints,
    }


def chart_profile(name, data):
    tl = timeline(data)
    t = [r["t"] for r in tl]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.4, 4.6), dpi=200, sharex=True)
    ax1.plot(t, [r["rps"] for r in tl], color="#2f5d8c", marker="o", markersize=3, label="RPS (запросов/с)")
    ax1.plot(t, [r["vusers"] for r in tl], color="#c0504d", linestyle="--", label="Новых ВП/с")
    ax1.axhline(10, color="grey", linewidth=0.7, linestyle=":")
    ax1.set_ylabel("Нагрузка")
    ax1.legend(fontsize=9, frameon=False, loc="upper right")
    ax1.grid(alpha=0.3)
    for key, style, lab in (("p50", "-", "p50"), ("p95", "--", "p95"), ("p99", ":", "p99")):
        ax2.plot(t, [r[key] for r in tl], linestyle=style, color="black", label=lab)
    ax2.set_ylabel("Время ответа, мс")
    ax2.set_xlabel("Время от начала теста, с")
    ax2.legend(fontsize=9, frameon=False, ncol=3, loc="upper right")
    ax2.grid(alpha=0.3)
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    p = CHARTS / f"{name}.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def chart_compare(summaries):
    names = [s["profile"].replace(" «", "\n«") for s in summaries]
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=200)
    x = range(len(names))
    w = 0.26
    for off, key, col, lab in ((-w, "median", "#c9d6e6", "Медиана"), (0, "p95", "#6f93bb", "p95"),
                               (w, "p99", "#2f5d8c", "p99")):
        vals = [s["rt"][key] for s in summaries]
        bars = ax.bar([i + off for i in x], vals, w, color=col, edgecolor="black", linewidth=0.5, label=lab)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 15, f"{b.get_height():.0f}",
                    ha="center", fontsize=8)
    ax.set_xticks(list(x), names)
    ax.set_ylabel("Время ответа, мс")
    ax.legend(fontsize=9, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    p = CHARTS / "compare.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def main():
    summaries = []
    for name in PROFILES:
        if not (RES / f"{name}.json").exists():
            print("нет результатов:", name)
            continue
        data = load(name)
        s = summarize(name, data)
        s["chart"] = str(chart_profile(name, data).relative_to(HERE))
        summaries.append(s)
        print(f"{s['profile']}: {s['requests']} запросов, пик {s['peak_rps']} RPS, "
              f"p95 {s['rt']['p95']} мс, ошибок {s['errors']}")
    if summaries:
        chart_compare(summaries)
    (RES / "summary.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
