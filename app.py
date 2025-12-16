from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

app = Flask(__name__)

# -------------------------
# Process dataclass
# -------------------------
@dataclass
class Proc:
    pid: str
    arrival: int
    burst: int
    priority: int = 0
    remaining: int = field(init=False)

    def __post_init__(self):
        self.remaining = self.burst

# -------------------------
# Algorithm implementations
# All algorithms accept List[Proc] (fresh copies recommended)
# They return a gantt list: List[Tuple[pid, start, end]]
# -------------------------
def fcfs(procs: List[Proc]):
    procs = sorted(procs, key=lambda p: p.arrival)
    time = 0
    gantt = []
    for p in procs:
        if time < p.arrival:
            gantt.append(("idle", time, p.arrival))
            time = p.arrival
        start = time
        end = time + p.burst
        gantt.append((p.pid, start, end))
        time = end
    return gantt

def sjf_nonpreemptive(procs: List[Proc]):
    procs = [Proc(p.pid, p.arrival, p.burst, p.priority) for p in procs]
    time = 0
    gantt = []
    ready = []
    remaining = procs[:]
    while remaining or ready:
        for p in remaining[:]:
            if p.arrival <= time:
                ready.append(p); remaining.remove(p)
        if not ready:
            next_t = min(remaining, key=lambda x: x.arrival).arrival
            gantt.append(("idle", time, next_t)); time = next_t; continue
        ready.sort(key=lambda x: (x.burst, x.arrival))
        p = ready.pop(0)
        start = time; end = time + p.burst
        gantt.append((p.pid, start, end))
        time = end
    return gantt

def sjf_preemptive(procs: List[Proc]):
    procs = [Proc(p.pid, p.arrival, p.burst, p.priority) for p in procs]
    time = 0
    gantt = []
    ready = []
    remaining = procs[:]
    current = None
    interval_start = None
    while remaining or ready or current:
        for p in remaining[:]:
            if p.arrival <= time:
                ready.append(p); remaining.remove(p)
        candidates = ready + ([current] if current else [])
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            if remaining:
                nxt = min(remaining, key=lambda x: x.arrival).arrival
                gantt.append(("idle", time, nxt)); time = nxt; continue
            break
        candidates.sort(key=lambda x: (x.remaining, x.arrival))
        chosen = candidates[0]
        if current is not None and chosen.pid != current.pid:
            gantt.append((current.pid, interval_start, time)); interval_start = None
        if chosen in ready: ready.remove(chosen)
        if chosen is not current:
            current = chosen
            interval_start = time
        # run 1 unit
        current.remaining -= 1
        time += 1
        if current.remaining == 0:
            gantt.append((current.pid, interval_start, time))
            current = None
            interval_start = None
    return gantt

def round_robin(procs: List[Proc], quantum: int = 2):
    procs = [Proc(p.pid, p.arrival, p.burst, p.priority) for p in procs]
    time = 0
    gantt = []
    queue = []
    remaining = procs[:]
    while remaining or queue:
        for p in remaining[:]:
            if p.arrival <= time:
                queue.append(p); remaining.remove(p)
        if not queue:
            if remaining:
                nxt = min(remaining, key=lambda x: x.arrival).arrival
                gantt.append(("idle", time, nxt)); time = nxt; continue
            break
        p = queue.pop(0)
        if p.remaining <= 0:
            continue
        run = min(quantum, p.remaining)
        start = time; end = time + run
        gantt.append((p.pid, start, end))
        p.remaining -= run
        time = end
        for q in remaining[:]:
            if q.arrival <= time:
                queue.append(q); remaining.remove(q)
        if p.remaining > 0:
            queue.append(p)
    return gantt

def priority_nonpreemptive(procs: List[Proc]):
    procs = [Proc(p.pid, p.arrival, p.burst, p.priority) for p in procs]
    time = 0; gantt = []; ready = []; remaining = procs[:]
    while remaining or ready:
        for p in remaining[:]:
            if p.arrival <= time:
                ready.append(p); remaining.remove(p)
        if not ready:
            if remaining:
                nxt = min(remaining, key=lambda x: x.arrival).arrival
                gantt.append(("idle", time, nxt)); time = nxt; continue
            break
        ready.sort(key=lambda x: (x.priority, x.arrival))
        p = ready.pop(0)
        start = time; end = time + p.burst
        gantt.append((p.pid, start, end))
        time = end
    return gantt

def priority_preemptive(procs: List[Proc]):
    procs = [Proc(p.pid, p.arrival, p.burst, p.priority) for p in procs]
    time = 0; gantt = []; ready = []; remaining = procs[:]
    current = None; interval_start = None
    while remaining or ready or current:
        for p in remaining[:]:
            if p.arrival <= time:
                ready.append(p); remaining.remove(p)
        candidates = ready + ([current] if current else [])
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            if remaining:
                nxt = min(remaining, key=lambda x: x.arrival).arrival
                gantt.append(("idle", time, nxt)); time = nxt; continue
            break
        candidates.sort(key=lambda x: (x.priority, x.arrival, x.remaining))
        chosen = candidates[0]
        if current is not None and chosen.pid != current.pid:
            gantt.append((current.pid, interval_start, time)); interval_start = None
        if chosen in ready: ready.remove(chosen)
        if chosen is not current:
            current = chosen; interval_start = time
        current.remaining -= 1; time += 1
        if current.remaining == 0:
            gantt.append((current.pid, interval_start, time)); current = None; interval_start = None
    return gantt

# -------------------------
# Metrics helper
# Builds metrics from gantt and process descriptor list
# -------------------------
def compute_metrics_from_gantt(proc_desc: List[Dict], gantt: List[Tuple[str, int, int]]):
    info = {p['pid']: {'arrival': int(p['arrival']), 'burst': int(p['burst']), 'priority': int(p.get('priority',0))} for p in proc_desc}
    starts = {pid: None for pid in info}
    completions = {pid: None for pid in info}
    for pid, s, e in gantt:
        if pid == 'idle': continue
        if starts[pid] is None:
            starts[pid] = s
        completions[pid] = e
    rows = []
    for pid, d in info.items():
        if starts[pid] is None or completions[pid] is None:
            # if a process never ran, mark NA and continue
            rows.append({'pid': pid, 'arrival': d['arrival'], 'burst': d['burst'],
                         'start': None, 'completion': None, 'TAT': None, 'WT': None, 'RT': None, 'priority': d['priority']})
            continue
        tat = completions[pid] - d['arrival']
        wt = tat - d['burst']
        rt = starts[pid] - d['arrival']
        rows.append({'pid': pid, 'arrival': d['arrival'], 'burst': d['burst'],
                     'start': starts[pid], 'completion': completions[pid], 'TAT': tat, 'WT': wt, 'RT': rt, 'priority': d['priority']})
    # averages (only for completed)
    completed = [r for r in rows if r['TAT'] is not None]
    avg_tat = sum(r['TAT'] for r in completed)/len(completed) if completed else None
    avg_wt  = sum(r['WT'] for r in completed)/len(completed) if completed else None
    avg_rt  = sum(r['RT'] for r in completed)/len(completed) if completed else None
    return rows, {'avg_tat': avg_tat, 'avg_wt': avg_wt, 'avg_rt': avg_rt}

# -------------------------
# Flask routes
# -------------------------
@app.route("/", methods=["GET"])
def index():
    # default example processes shown in textarea
    example = "P1,0,8,2\nP2,1,4,1\nP3,2,9,3\nP4,3,5,2"
    return render_template("index.html", example=example)

@app.route("/simulate", methods=["POST"])
def simulate():
    # parse form
    processes_text = request.form.get("processes", "")
    algorithm = request.form.get("algorithm", "fcfs")
    quantum = int(request.form.get("quantum", "2"))

    # parse CSV-like input: PID,arrival,burst,priority (priority optional)
    proc_desc = []
    for line in processes_text.strip().splitlines():
        if not line.strip():
            continue
        parts = [x.strip() for x in line.split(",")]
        if len(parts) < 3:
            continue
        pid = parts[0]
        arrival = int(parts[1])
        burst = int(parts[2])
        priority = int(parts[3]) if len(parts) >= 4 else 0
        proc_desc.append({'pid': pid, 'arrival': arrival, 'burst': burst, 'priority': priority})

    # create Proc objects
    proc_objs = [Proc(d['pid'], d['arrival'], d['burst'], d['priority']) for d in proc_desc]

    # select algorithm
    if algorithm == "fcfs":
        gantt = fcfs(proc_objs)
    elif algorithm == "sjf-np":
        gantt = sjf_nonpreemptive(proc_objs)
    elif algorithm == "sjf-p":
        gantt = sjf_preemptive(proc_objs)
    elif algorithm == "rr":
        gantt = round_robin(proc_objs, quantum=quantum)
    elif algorithm == "priority-np":
        gantt = priority_nonpreemptive(proc_objs)
    elif algorithm == "priority-p":
        gantt = priority_preemptive(proc_objs)
    else:
        gantt = fcfs(proc_objs)

    # compute metrics
    rows, avgs = compute_metrics_from_gantt(proc_desc, gantt)

    # convert gantt to JSON-friendly
    gantt_json = [{'pid': pid, 'start': s, 'end': e} for (pid, s, e) in gantt]

    return render_template("index.html",
                           example="\n".join(f"{r['pid']},{r['arrival']},{r['burst']},{r.get('priority',0)}" for r in proc_desc),
                           gantt_json=json.dumps(gantt_json),
                           rows=rows,
                           avgs=avgs,
                           chosen_algorithm=algorithm,
                           quantum=quantum)

if __name__ == "__main__":
    app.run()

