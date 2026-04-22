"""
INFB6074 - Infraestructura para Ciencia de Datos
Actividad Semana 2: Benchmarking de Jerarquía de Memoria e I/O
Universidad Tecnológica Metropolitana
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time
import os
import psutil
import platform
import random
import json
import csv
from pathlib import Path

# ─── Configuración de rutas ───────────────────────────────────────────────────
BASE_DIR    = Path.cwd()
DATA_DIR    = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
VIZ_DIR     = BASE_DIR / "visualizations"

for d in [DATA_DIR, RESULTS_DIR, VIZ_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Paleta de colores consistente ────────────────────────────────────────────
C1, C2, C3, C4 = "#2563EB", "#16A34A", "#DC2626", "#D97706"
STYLE = {
    "axes.facecolor":  "#F8FAFC",
    "figure.facecolor":"#FFFFFF",
    "axes.grid":       True,
    "grid.alpha":      0.4,
    "font.family":     "DejaVu Sans",
}
plt.rcParams.update(STYLE)

# ─── 0. Documentar entorno experimental ───────────────────────────────────────
def get_env_info():
    cpu = psutil.cpu_count(logical=True)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    info = {
        "OS":           platform.system() + " " + platform.release(),
        "Arquitectura": platform.machine(),
        "Python":       platform.python_version(),
        "CPUs (lógicos)":       cpu,
        "RAM total (GB)":       round(mem.total / 1e9, 2),
        "RAM disponible (GB)":  round(mem.available / 1e9, 2),
        "Disco total (GB)":     round(disk.total / 1e9, 2),
        "Disco libre (GB)":     round(disk.free / 1e9, 2),
        "NumPy":        np.__version__,
        "Pandas":       pd.__version__,
    }
    with open(RESULTS_DIR / "entorno.json", "w") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print("=== Entorno Experimental ===")
    for k, v in info.items():
        print(f"  {k}: {v}")
    return info

env = get_env_info()

# ─── EXPERIMENTO A: Jerarquía de Memoria ──────────────────────────────────────
print("\n=== Experimento A: Jerarquía de Memoria ===")

SIZES_MB = [1, 10, 50, 100, 250, 500]   # ≥5 tamaños
results_a = []

for mb in SIZES_MB:
    n_floats = (mb * 1024 * 1024) // 8   # float64 = 8 bytes

    # ── Operación en RAM ──
    arr = np.random.rand(n_floats)
    t0 = time.perf_counter()
    _ = arr.sum()                         # operación sobre todo el array
    t_ram = time.perf_counter() - t0
    tp_ram = mb / t_ram                   # throughput MB/s

    # ── Escritura en disco ──
    fpath = DATA_DIR / f"bench_{mb}mb.bin"
    t0 = time.perf_counter()
    arr.tofile(str(fpath))
    t_write = time.perf_counter() - t0
    tp_write = mb / t_write

    # ── Lectura desde disco ──
    t0 = time.perf_counter()
    arr2 = np.fromfile(str(fpath), dtype=np.float64)
    t_read = time.perf_counter() - t0
    tp_read = mb / t_read

    results_a.append({
        "Tamaño_MB":    mb,
        "T_RAM_s":      round(t_ram,   6),
        "T_Escritura_s":round(t_write, 4),
        "T_Lectura_s":  round(t_read,  4),
        "TP_RAM_MBs":   round(tp_ram,  2),
        "TP_Escritura_MBs": round(tp_write, 2),
        "TP_Lectura_MBs":   round(tp_read,  2),
    })
    print(f"  {mb:>4} MB | RAM {t_ram:.6f}s | Write {t_write:.4f}s | Read {t_read:.4f}s")

df_a = pd.DataFrame(results_a)
df_a.to_csv(RESULTS_DIR / "experimento_A.csv", index=False)

# Visualización A
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Experimento A – Jerarquía de Memoria", fontsize=14, fontweight="bold")

ax = axes[0]
ax.plot(df_a["Tamaño_MB"], df_a["T_RAM_s"],        marker="o", color=C1, label="RAM (operación)")
ax.plot(df_a["Tamaño_MB"], df_a["T_Lectura_s"],    marker="s", color=C3, label="Disco – Lectura")
ax.plot(df_a["Tamaño_MB"], df_a["T_Escritura_s"],  marker="^", color=C4, label="Disco – Escritura")
ax.set_xlabel("Tamaño (MB)"); ax.set_ylabel("Tiempo (s)"); ax.legend()
ax.set_title("Tiempo de operación vs Tamaño")

ax2 = axes[1]
x = np.arange(len(df_a))
w = 0.28
ax2.bar(x - w, df_a["TP_RAM_MBs"],       width=w, color=C1, label="RAM")
ax2.bar(x,     df_a["TP_Lectura_MBs"],   width=w, color=C3, label="Disco – Lectura")
ax2.bar(x + w, df_a["TP_Escritura_MBs"], width=w, color=C4, label="Disco – Escritura")
ax2.set_xticks(x); ax2.set_xticklabels(df_a["Tamaño_MB"])
ax2.set_xlabel("Tamaño (MB)"); ax2.set_ylabel("Throughput (MB/s)"); ax2.legend()
ax2.set_title("Throughput por nivel de memoria")

plt.tight_layout()
plt.savefig(VIZ_DIR / "exp_A_memoria.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Gráfico A guardado")

# ─── EXPERIMENTO B: Acceso Secuencial vs Aleatorio ────────────────────────────
print("\n=== Experimento B: Acceso Secuencial vs Aleatorio ===")

N_ROWS = 300_000
df_test = pd.DataFrame({
    "id":      np.arange(N_ROWS),
    "valor_a": np.random.rand(N_ROWS),
    "valor_b": np.random.randn(N_ROWS),
    "categoria": np.random.choice(["A","B","C","D"], N_ROWS),
    "timestamp": pd.date_range("2024-01-01", periods=N_ROWS, freq="s"),
})

csv_path     = DATA_DIR / "test_data.csv"
parquet_path = DATA_DIR / "test_data.parquet"

df_test.to_csv(str(csv_path), index=False)
df_test.to_parquet(str(parquet_path), index=False)

results_b = []
N_SAMPLES = 5_000   # índices aleatorios a leer

def bench_seq_csv(path):
    t0 = time.perf_counter()
    df = pd.read_csv(path)
    _ = df["valor_a"].sum()
    return time.perf_counter() - t0

def bench_seq_parquet(path):
    t0 = time.perf_counter()
    df = pd.read_parquet(path, columns=["valor_a"])
    _ = df["valor_a"].sum()
    return time.perf_counter() - t0

def bench_rand_csv(path, indices):
    t0 = time.perf_counter()
    df = pd.read_csv(path, skiprows=lambda i: i != 0 and (i - 1) not in set(indices))
    return time.perf_counter() - t0

def bench_rand_parquet(path, indices):
    t0 = time.perf_counter()
    df = pd.read_parquet(path)
    _ = df.iloc[indices]
    return time.perf_counter() - t0

indices = sorted(random.sample(range(N_ROWS), N_SAMPLES))

for trial in range(3):
    t_seq_csv     = bench_seq_csv(csv_path)
    t_seq_parquet = bench_seq_parquet(parquet_path)
    t_rand_csv    = bench_rand_csv(csv_path, indices)
    t_rand_parquet= bench_rand_parquet(parquet_path, indices)
    results_b.append({
        "Trial": trial + 1,
        "Seq_CSV_s":      round(t_seq_csv,    4),
        "Seq_Parquet_s":  round(t_seq_parquet, 4),
        "Rand_CSV_s":     round(t_rand_csv,    4),
        "Rand_Parquet_s": round(t_rand_parquet,4),
    })
    print(f"  Trial {trial+1}: SeqCSV={t_seq_csv:.4f}s | SeqParquet={t_seq_parquet:.4f}s | "
          f"RandCSV={t_rand_csv:.4f}s | RandParquet={t_rand_parquet:.4f}s")

df_b = pd.DataFrame(results_b)
df_b.to_csv(RESULTS_DIR / "experimento_B.csv", index=False)
means_b = df_b.mean(numeric_only=True)

# Tamaños de archivo
csv_size_mb     = csv_path.stat().st_size / 1e6
parquet_size_mb = parquet_path.stat().st_size / 1e6

# Visualización B
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Experimento B – Acceso Secuencial vs Aleatorio", fontsize=14, fontweight="bold")

ax = axes[0]
cats  = ["CSV\nSecuencial", "Parquet\nSecuencial", "CSV\nAleatorio", "Parquet\nAleatorio"]
vals  = [means_b["Seq_CSV_s"], means_b["Seq_Parquet_s"],
         means_b["Rand_CSV_s"], means_b["Rand_Parquet_s"]]
colors = [C3, C1, C3, C1]
bars = ax.bar(cats, vals, color=colors, width=0.55, edgecolor="white")
ax.bar_label(bars, fmt="%.3f s", padding=3, fontsize=9)
ax.set_ylabel("Tiempo promedio (s)"); ax.set_title("Tiempo por tipo de acceso y formato")

ax2 = axes[1]
formats = ["CSV", "Parquet"]
sizes   = [csv_size_mb, parquet_size_mb]
ax2.bar(formats, sizes, color=[C3, C1], width=0.4, edgecolor="white")
ax2.set_ylabel("Tamaño en disco (MB)"); ax2.set_title("Tamaño del archivo en disco")
ax2.bar_label(ax2.containers[0], fmt="%.1f MB", padding=3, fontsize=10)

plt.tight_layout()
plt.savefig(VIZ_DIR / "exp_B_acceso.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Gráfico B guardado")

# ─── EXPERIMENTO C: Detección de Cuellos de Botella ──────────────────────────
print("\n=== Experimento C: Cuellos de Botella en Pipeline ===")

# 6+ configuraciones: variando tamaño y tipo de transformación
CONFIGS = [
    {"name": "Config 1: Small + Simple",   "rows": 50_000,  "transform": "simple"},
    {"name": "Config 2: Small + Complex",  "rows": 50_000,  "transform": "complex"},
    {"name": "Config 3: Medium + Simple",  "rows": 200_000, "transform": "simple"},
    {"name": "Config 4: Medium + Complex", "rows": 200_000, "transform": "complex"},
    {"name": "Config 5: Large + Simple",   "rows": 500_000, "transform": "simple"},
    {"name": "Config 6: Large + Complex",  "rows": 500_000, "transform": "complex"},
    {"name": "Config 7: XLarge + Simple",  "rows": 1_000_000,"transform": "simple"},
    {"name": "Config 8: XLarge + Complex", "rows": 1_000_000,"transform": "complex"},
]

results_c = []
for cfg in CONFIGS:
    rows = cfg["rows"]
    ttype = cfg["transform"]

    # ── Ingesta ──
    t0 = time.perf_counter()
    df = pd.DataFrame({
        "x": np.random.rand(rows),
        "y": np.random.randn(rows),
        "cat": np.random.choice(list("ABCDE"), rows),
    })
    t_ingest = time.perf_counter() - t0

    # ── Transformación ──
    t0 = time.perf_counter()
    if ttype == "simple":
        df["z"] = df["x"] * 2 + df["y"]
    else:  # complex
        df["z"] = np.log1p(np.abs(df["x"])) * np.exp(-df["y"]**2 / 2)
        df["grp_mean"] = df.groupby("cat")["x"].transform("mean")
        df["rank"] = df["z"].rank(pct=True)
    t_transform = time.perf_counter() - t0

    # ── Almacenamiento ──
    out_path = DATA_DIR / f"pipeline_out_{rows}_{ttype}.parquet"
    t0 = time.perf_counter()
    df.to_parquet(str(out_path), index=False)
    t_store = time.perf_counter() - t0

    total = t_ingest + t_transform + t_store
    bottleneck = max(("Ingesta", t_ingest), ("Transformación", t_transform), ("Almacenamiento", t_store), key=lambda x: x[1])[0]

    results_c.append({
        "Configuración": cfg["name"],
        "Filas":          rows,
        "Transformación": ttype,
        "T_Ingesta_s":    round(t_ingest,    4),
        "T_Transform_s":  round(t_transform, 4),
        "T_Store_s":      round(t_store,     4),
        "T_Total_s":      round(total,       4),
        "Cuello_de_Botella": bottleneck,
    })
    print(f"  {cfg['name']} | Ingesta={t_ingest:.4f}s | Transform={t_transform:.4f}s | "
          f"Store={t_store:.4f}s | Botella={bottleneck}")

df_c = pd.DataFrame(results_c)
df_c.to_csv(RESULTS_DIR / "experimento_C.csv", index=False)

# Visualización C
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Experimento C – Detección de Cuellos de Botella", fontsize=14, fontweight="bold")

ax = axes[0]
labels_c = [f"C{i+1}" for i in range(len(df_c))]
x_c = np.arange(len(df_c))
w = 0.28
ax.bar(x_c - w, df_c["T_Ingesta_s"],   width=w, color=C1, label="Ingesta")
ax.bar(x_c,     df_c["T_Transform_s"], width=w, color=C3, label="Transformación")
ax.bar(x_c + w, df_c["T_Store_s"],     width=w, color=C4, label="Almacenamiento")
ax.set_xticks(x_c); ax.set_xticklabels(labels_c, rotation=30, ha="right")
ax.set_ylabel("Tiempo (s)"); ax.legend(); ax.set_title("Tiempo por etapa del pipeline")

ax2 = axes[1]
bottlenecks = df_c["Cuello_de_Botella"].value_counts()
ax2.pie(bottlenecks.values, labels=bottlenecks.index,
        colors=[C1, C3, C4][:len(bottlenecks)],
        autopct="%1.0f%%", startangle=90, textprops={"fontsize": 11})
ax2.set_title("Distribución de cuellos de botella")

plt.tight_layout()
plt.savefig(VIZ_DIR / "exp_C_pipeline.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Gráfico C guardado")

# ─── EXPERIMENTO D: Batch vs Streaming ────────────────────────────────────────
print("\n=== Experimento D: Batch vs Streaming ===")

BATCH_SIZES  = [100, 500, 1000, 5000]
TOTAL_EVENTS = 10_000
results_d = []

def process_event(event):
    """Simula procesamiento de un evento."""
    return {"id": event["id"], "valor": event["valor"] ** 0.5, "processed": True}

for bs in BATCH_SIZES:
    events = [{"id": i, "valor": random.random()} for i in range(TOTAL_EVENTS)]

    # ── Batch ──
    t0 = time.perf_counter()
    batches = [events[i:i+bs] for i in range(0, len(events), bs)]
    processed_batch = []
    for batch in batches:
        processed_batch.extend([process_event(e) for e in batch])
    t_batch = time.perf_counter() - t0
    tp_batch = TOTAL_EVENTS / t_batch   # eventos/s

    # ── Streaming (event-by-event) ──
    first_latency_stream = None
    t0_stream = time.perf_counter()
    for idx, event in enumerate(events):
        result = process_event(event)
        if idx == 0:
            first_latency_stream = time.perf_counter() - t0_stream
    t_stream = time.perf_counter() - t0_stream
    tp_stream = TOTAL_EVENTS / t_stream

    # Latencia de primer resultado en batch
    t0_lat = time.perf_counter()
    first_batch = events[:bs]
    _ = [process_event(e) for e in first_batch]
    first_latency_batch = time.perf_counter() - t0_lat

    results_d.append({
        "Batch_Size":        bs,
        "T_Batch_s":         round(t_batch,               4),
        "T_Streaming_s":     round(t_stream,              4),
        "TP_Batch_eps":      round(tp_batch,              1),
        "TP_Streaming_eps":  round(tp_stream,             1),
        "Latencia_Batch_s":  round(first_latency_batch,   6),
        "Latencia_Stream_s": round(first_latency_stream,  6),
    })
    print(f"  BatchSize={bs:>5} | Batch={t_batch:.4f}s ({tp_batch:.0f} ev/s) | "
          f"Stream={t_stream:.4f}s ({tp_stream:.0f} ev/s)")

df_d = pd.DataFrame(results_d)
df_d.to_csv(RESULTS_DIR / "experimento_D.csv", index=False)

# Visualización D
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Experimento D – Batch vs Streaming", fontsize=14, fontweight="bold")

ax = axes[0]
ax.plot(df_d["Batch_Size"], df_d["T_Batch_s"],    marker="o", color=C1, label="Batch")
ax.plot(df_d["Batch_Size"], df_d["T_Streaming_s"],marker="s", color=C2, label="Streaming")
ax.set_xlabel("Tamaño de lote"); ax.set_ylabel("Tiempo total (s)")
ax.set_title("Tiempo total de procesamiento"); ax.legend()

ax2 = axes[1]
ax2.plot(df_d["Batch_Size"], df_d["TP_Batch_eps"],    marker="o", color=C1, label="Batch")
ax2.plot(df_d["Batch_Size"], df_d["TP_Streaming_eps"],marker="s", color=C2, label="Streaming")
ax2.set_xlabel("Tamaño de lote"); ax2.set_ylabel("Throughput (eventos/s)")
ax2.set_title("Throughput"); ax2.legend()

ax3 = axes[2]
x_d = np.arange(len(df_d))
w = 0.38
ax3.bar(x_d - w/2, df_d["Latencia_Batch_s"]  * 1000, width=w, color=C1, label="Batch (ms)")
ax3.bar(x_d + w/2, df_d["Latencia_Stream_s"] * 1000, width=w, color=C2, label="Streaming (ms)")
ax3.set_xticks(x_d); ax3.set_xticklabels(df_d["Batch_Size"])
ax3.set_xlabel("Tamaño de lote"); ax3.set_ylabel("Latencia primer resultado (ms)")
ax3.set_title("Latencia al primer resultado"); ax3.legend()

plt.tight_layout()
plt.savefig(VIZ_DIR / "exp_D_batch_streaming.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Gráfico D guardado")

print("\n✓ Todos los experimentos completados.")
print(f"  Resultados: {RESULTS_DIR}")
print(f"  Visualizaciones: {VIZ_DIR}")
