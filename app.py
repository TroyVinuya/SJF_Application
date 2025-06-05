# app.py

import random
import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output, State
import plotly.express as px

# ──────────────────────────────────────────────────────────────────────────────
# 1) SJF Logic (core computation)
# ──────────────────────────────────────────────────────────────────────────────
def compute_sjf(n):
    """
    Generates n processes with random arrival (0–30) and burst (1–30),
    then runs non-preemptive SJF and returns a DataFrame with columns:
      ['id', 'arrival', 'burst', 'start', 'completion', 'tat', 'wt']
    plus:
      - schedule_order: list of IDs in execution order
      - total_time: final completion time
      - avg_wt, avg_tat
    """
    # 1) Generate random processes
    processes = []
    for i in range(n):
        pid = f"P{i+1}"
        arrival = random.randint(0, 30)
        burst = random.randint(1, 30)
        processes.append({
            "id": pid,
            "arrival": arrival,
            "burst": burst,
            "start": None,
            "completion": None,
            "tat": None,
            "wt": None
        })

    # 2) SJF scheduling
    time = 0
    remaining = processes.copy()
    schedule_order = []

    while remaining:
        # a) Find all arrived processes at current time
        arrived = [p for p in remaining if p["arrival"] <= time]
        if not arrived:
            # No one has arrived yet → jump to earliest arrival
            time = min(p["arrival"] for p in remaining)
            arrived = [p for p in remaining if p["arrival"] <= time]

        # b) Pick the one with smallest burst
        current = min(arrived, key=lambda x: x["burst"])
        schedule_order.append(current["id"])

        # c) Compute start, completion, tat, wt
        current["start"] = time
        finish = time + current["burst"]
        current["completion"] = finish
        current["tat"] = current["completion"] - current["arrival"]
        current["wt"] = current["tat"] - current["burst"]

        # d) Advance time and remove from pool
        time = finish
        remaining.remove(current)

    total_time = time

    # 3) Build a DataFrame sorted by numeric ID (for consistent display order)
    df = pd.DataFrame(processes).sort_values(key=lambda col: col["id"].apply(lambda s: int(s[1:])))
    avg_wt = df["wt"].mean()
    avg_tat = df["tat"].mean()

    return df, schedule_order, total_time, avg_wt, avg_tat


# ──────────────────────────────────────────────────────────────────────────────
# 2) Dash App Layout
# ──────────────────────────────────────────────────────────────────────────────
app = Dash(__name__)
server = app.server  # expose the Flask server if you want to deploy on Gunicorn

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "padding": "20px"},
    children=[
        html.H2("SJF Simulator (Web Version)", style={"textAlign": "center"}),

        # ------- Number of Jobs Dropdown and Button -------
        html.Div(
            style={"display": "flex", "alignItems": "center", "marginBottom": "20px"},
            children=[
                html.Label("Number of Jobs:", style={"marginRight": "10px", "fontWeight": "bold"}),
                dcc.Dropdown(
                    id="num-job-dropdown",
                    options=[{"label": str(i), "value": i} for i in (4, 5)],
                    value=4,
                    clearable=False,
                    style={"width": "80px"}
                ),
                html.Button(
                    "Generate Data",
                    id="generate-button",
                    n_clicks=0,
                    style={"marginLeft": "20px", "padding": "6px 12px"}
                ),
            ]
        ),

        # ------- Pool Table Section -------
        html.Div(
            style={"border": "2px solid #028174", "borderRadius": "8px", "padding": "10px", "backgroundColor": "#FFFFFF", "marginBottom": "20px"},
            children=[
                html.H4("Pool Table (Process Data)", style={"marginTop": "0"}),
                dash_table.DataTable(
                    id="pool-table",
                    columns=[
                        {"name": "Process #",      "id": "id"},
                        {"name": "Arrival Time",   "id": "arrival"},
                        {"name": "Burst Time",     "id": "burst"},
                        {"name": "Start Time",     "id": "start"},
                        {"name": "Completion Time","id": "completion"},
                        {"name": "Turnaround Time","id": "tat"},
                        {"name": "Wait Time",      "id": "wt"},
                    ],
                    data=[],
                    style_cell={"textAlign": "center", "padding": "6px"},
                    style_header={
                        "backgroundColor": "#028174",
                        "fontWeight": "bold",
                        "color": "white"
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#F9F9F9"},
                    ],
                    style_table={"overflowX": "auto"},
                    page_size=10,
                )
            ]
        ),

        # ------- CPU Statistics & Ready Queue -------
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    style={"flex": "1", "border": "2px solid #028174", "borderRadius": "8px", "padding": "10px", "backgroundColor": "#FFFFFF"},
                    children=[
                        html.H4("CPU Statistics", style={"marginTop": "0"}),
                        html.Div(id="cpu-stats", style={"fontSize": "16px", "lineHeight": "1.5"})
                    ]
                ),
                html.Div(
                    style={"flex": "1", "border": "2px solid #028174", "borderRadius": "8px", "padding": "10px", "backgroundColor": "#FFFFFF"},
                    children=[
                        html.H4("Ready Queue", style={"marginTop": "0"}),
                        html.Div(id="ready-queue", style={"fontSize": "16px", "whiteSpace": "nowrap"})
                    ]
                ),
            ]
        ),

        # ------- Gantt Chart -------
        html.Div(
            style={"border": "2px solid #028174", "borderRadius": "8px", "padding": "10px", "backgroundColor": "#FFFFFF"},
            children=[
                html.H4("Gantt Chart", style={"marginTop": "0"}),
                dcc.Graph(id="gantt-chart", config={"displayModeBar": False})
            ]
        ),
    ]
)


# ──────────────────────────────────────────────────────────────────────────────
# 3) Callbacks
# ──────────────────────────────────────────────────────────────────────────────
@app.callback(
    [
        Output("pool-table", "data"),
        Output("cpu-stats", "children"),
        Output("ready-queue", "children"),
        Output("gantt-chart", "figure"),
    ],
    [Input("generate-button", "n_clicks")],
    [State("num-job-dropdown", "value")]
)
def update_simulation(n_clicks, num_jobs):
    """
    Whenever the 'Generate Data' button is clicked, regenerate random SJF data—
    recompute the tables, stats, queue, and Gantt chart.
    """
    if n_clicks is None or num_jobs is None:
        # Initial empty state
        return [], "", "", {}

    # 1) Compute SJF for 'num_jobs' processes
    df, schedule_order, total_time, avg_wt, avg_tat = compute_sjf(num_jobs)

    # 2) Pool table data (include all columns)
    pool_data = df.to_dict("records")

    # 3) CPU stats (N, total_time, avg_wt, avg_tat)
    cpu_stats_children = [
        html.P(f"Number of Jobs: {num_jobs}"),
        html.P(f"Total Completion Time: {total_time}"),
        html.P(f"Average Waiting Time: {avg_wt:.2f}"),
        html.P(f"Average Turnaround Time: {avg_tat:.2f}"),
    ]

    # 4) Ready queue display (just show the schedule order)
    ready_queue_str = " → ".join(schedule_order)

    # 5) Build Gantt chart via Plotly Express timeline
    #    We use columns "start" and "completion" from df:
    gantt_df = df.copy()
    gantt_df["finish"] = gantt_df["completion"]

    fig = px.timeline(
        gantt_df,
        x_start="start",
        x_end="finish",
        y="id",
        color="id",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="",
    )
    fig.update_yaxes(autorange="reversed")  # so P1 is on top
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        xaxis_title="Time",
        yaxis_title="Process"
    )

    return pool_data, cpu_stats_children, ready_queue_str, fig


# ──────────────────────────────────────────────────────────────────────────────
# 4) Run the App
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run_server(debug=True)
