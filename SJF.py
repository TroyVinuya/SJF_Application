import tkinter as tk
import random
import customtkinter as ctk



root = ctk.CTk()
root.geometry('1000x700')
root.title('SJF Simulator')

# Global declaration
process_data = []
schedule_order = []
total_time = 0
canvas = None
pool_table_widgets = []
queue_label = None
job_labels = []
color_map = {}


# Functions

def job(selected_value):
    numJob.config(text=f"Number of Jobs:  {selected_value}")


# Generate random data
def generate_data():
    global process_data, schedule_order, total_time, color_map

    # Clear previous data and graphics
    clear_tables_and_canvas()

    n = int(combo_box_numJob.get())
    process_data = []

    # 2) Generate randomized arrival and burst time max 30
    for i in range(n):
        pid = f"P{i+1}"
        arrival = random.randint(0, 30)
        burst = random.randint(1, 30)
        process_data.append({
            "id": pid,
            "arrival": arrival,
            "burst": burst,
            "completion": 0,
            "tat": 0,
            "wt": 0
        })

    # SJF computation
    time = 0
    remaining = process_data.copy()
    schedule_order = []
    while remaining:
        # Find all arrived processes at current time
        arrived = [p for p in remaining if p["arrival"] <= time]
        if not arrived:
            # If none arrived, jump time to next arrival
            time = min(p["arrival"] for p in remaining)
            arrived = [p for p in remaining if p["arrival"] <= time]

        # Select entity with smallest burst
        current = min(arrived, key=lambda x: x["burst"])
        schedule_order.append(current["id"])

        # Compute its metrics
        start = time
        finish = time + current["burst"]
        current["completion"] = finish
        current["tat"] = finish - current["arrival"]
        current["wt"] = current["tat"] - current["burst"]

        # Advance time and remove from remaining
        time = finish
        remaining.remove(current)

    total_time = time

    # Fill the Pool table
    process_data.sort(key=lambda x: int(x["id"][1:]))  # Sort by numeric part of ID

    for r in range(len(process_data) + 1):
        pool_table.grid_rowconfigure(r, weight=1)

    # Insert header row
    # Insert data rows starting at row=1
    for i, pdata in enumerate(process_data, start=1):
        # Create labels for each column with visible cell borders
        lbl_id    = tk.Label(pool_table, text=pdata["id"],       bg="#FFFFFF", borderwidth=1, relief="solid")
        lbl_arr   = tk.Label(pool_table, text=str(pdata["arrival"]), bg="#FFFFFF", borderwidth=1, relief="solid")
        lbl_burst = tk.Label(pool_table, text=str(pdata["burst"]),   bg="#FFFFFF", borderwidth=1, relief="solid")
        lbl_comp  = tk.Label(pool_table, text=str(pdata["completion"]), bg="#FFFFFF", borderwidth=1, relief="solid")
        lbl_tat   = tk.Label(pool_table, text=str(pdata["tat"]),    bg="#FFFFFF", borderwidth=1, relief="solid")
        lbl_wt    = tk.Label(pool_table, text=str(pdata["wt"]),    bg="#FFFFFF", borderwidth=1, relief="solid")

        lbl_id.grid(row=i, column=0, sticky="nsew")
        lbl_arr.grid(row=i, column=1, sticky="nsew")
        lbl_burst.grid(row=i, column=2, sticky="nsew")
        lbl_comp.grid(row=i, column=3, sticky="nsew")
        lbl_tat.grid(row=i, column=4, sticky="nsew")
        lbl_wt.grid(row=i, column=5, sticky="nsew")

        pool_table_widgets.append((lbl_id, lbl_arr, lbl_burst, lbl_comp, lbl_tat, lbl_wt))

    # 5) Compute average metrics and fill CPU table
    avg_wt = sum(p["wt"] for p in process_data) / n
    avg_tat = sum(p["tat"] for p in process_data) / n

    value_job.config(text=str(n))
    value_time.config(text=str(total_time))
    value_avg_wt.config(text=f"{avg_wt:.2f}")
    value_avg_tat.config(text=f"{avg_tat:.2f}")

    # 6) Populate the Queue table with execution order as initial ready queue display
    queue_label.config(text="Ready Queue: " + " → ".join(schedule_order))

    # 7) Prepare colors for Gantt chart (each process gets a distinct color)
    base_colors = ["#B22222", "#228B22", "#1E90FF", "#DAA520", "#8A2BE2"]
    color_map = {f"P{i+1}": base_colors[i % len(base_colors)] for i in range(n)}

    # Enable Simulate button now that data is generated
    simulate_btn.configure(state="normal")



# Run the simulation: animate Gantt chart drawing and update ready queue

def simulate():
    simulate_btn.configure(state="disabled")
    pause_btn.configure(state="normal")

    # Clear canvas if anything exists
    gantt_canvas.delete("all")

    # Compute scale factor so that all rectangles fit in canvas width
    if total_time == 0:
        return
    c_width = gantt_canvas.winfo_width()
    scale = c_width / total_time

    current_x = 0
    delay = 1500  # milliseconds per unit burst

    def draw_step(step_index):
        nonlocal current_x
        if step_index >= len(schedule_order):
            # Finished drawing all steps
            pause_btn.configure(state="disabled")
            return

        pid = schedule_order[step_index]
        # Find this process's burst time
        burst = next(p["burst"] for p in process_data if p["id"] == pid)
        rect_width = burst * scale
        x0 = current_x
        x1 = current_x + rect_width

        # Compute vertical centering inside the 80px-high canvas
        canvas_height = gantt_canvas.winfo_height()
        if canvas_height <= 1:
            canvas_height = 80  # fallback if not yet fully rendered
        bar_height = 50
        y0 = (canvas_height - bar_height) / 2
        y1 = y0 + bar_height

        # Draw rectangle centered vertically
        color = color_map[pid]
        gantt_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        # Draw process ID text in the vertical center of that bar
        gantt_canvas.create_text((x0 + x1) / 2, canvas_height / 2,
                                 text=pid, fill="white", font=("Arial", 12, "bold"))

        # Update ready queue display: remove this pid from queue
        remaining_queue = schedule_order[step_index + 1:]
        queue_label.config(text="Ready Queue: " + " → ".join(remaining_queue if remaining_queue else ["--"]))

        current_x = x1

        # Schedule next step
        root.after(delay, lambda: draw_step(step_index + 1))

    # Start drawing steps from index 0
    draw_step(0)



# Pause simulation (simply disables further animation)

def pause():
    # Simply disable pause; since animation is sequential via after(), it won't progress further
    pause_btn.configure(state="disabled")
    simulate_btn.configure(state="normal")



# Reset all tables and Gantt chart

def reset():
    global process_data, schedule_order, total_time
    process_data = []
    schedule_order = []
    total_time = 0
    clear_tables_and_canvas()
    combo_box_numJob.set("4")
    numJob.config(text="Number of Jobs: ")
    simulate_btn.configure(state="disabled")
    pause_btn.configure(state="disabled")



# Helper: Clear Pool, CPU, Queue tables, and Gantt canvas

def clear_tables_and_canvas():
    # Clear Pool table data rows
    for widgets in pool_table_widgets:
        for w in widgets:
            w.destroy()
    pool_table_widgets.clear()

    # Reset CPU values
    value_job.config(text="0")
    value_time.config(text="0")
    value_avg_wt.config(text="0")
    value_avg_tat.config(text="0")

    # Clear queue label
    queue_label.config(text="Ready Queue: ")

    # Clear Gantt canvas
    gantt_canvas.delete("all")



# UI Layout


# Number of Jobs label and combo box
numJob = tk.Label(root, text="Number of Jobs: ")
numJob.place(x=100, y=550)

combo_box_numJob = ctk.CTkComboBox(
    master=root,
    values=["4", "5"],
    width=100,
    height=30,
    corner_radius=8,
    fg_color="#F0F0F0",
    button_color="#028174",
    button_hover_color="#026F64",
    text_color="#000000",
    dropdown_fg_color="#92DE8B",
    dropdown_hover_color="#0AB68B",
    dropdown_text_color="#FFFFFF"
)
combo_box_numJob.place(x=100, y=575)
combo_box_numJob.set("4")
combo_box_numJob.configure(command=job)


# Pool Table (Process Data)

poolFrame = ctk.CTkFrame(root, width=975, height=250, corner_radius=15, fg_color="#028174")
poolFrame.place(x=10, y=50)

pool_table = ctk.CTkFrame(poolFrame, width=955, height=230, corner_radius=15, fg_color="#FFFFFF")
pool_table.pack(padx=10, pady=10)
pool_table.grid_propagate(False)

# Configure 6 columns (Process #, Arrival, Burst, Completion, Turnaround, Wait)
for col in range(6):
    pool_table.grid_columnconfigure(col, weight=1)

# Header row
headers = ["Process #", "Arrival Time", "Burst Time", "Completion Time", "Turnaround Time", "Wait Time"]
for idx, text in enumerate(headers):
    lbl = tk.Label(pool_table, text=text, bg="#FFFFFF", font=("Arial", 10, "bold"))
    lbl.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")


# Gantt Chart Frame

ganttFrame = ctk.CTkFrame(root, width=975, height=100, corner_radius=15, fg_color="#028174")
ganttFrame.place(x=10, y=310)

gantt_table = ctk.CTkFrame(ganttFrame, width=955, height=80, corner_radius=15, fg_color="#FFFFFF")
gantt_table.pack(padx=10, pady=10)
gantt_table.grid_propagate(False)

# Inside gantt_table, place a Canvas for drawing rectangles
gantt_canvas = tk.Canvas(gantt_table, width=955, height=80, bg="#FFFFFF", highlightthickness=0)
gantt_canvas.place(x=0, y=0)


# CPU Table (Statistics)

cpuFrame = ctk.CTkFrame(root, width=480, height=100, corner_radius=15, fg_color="#028174")
cpuFrame.place(x=10, y=425)

cpu_table = ctk.CTkFrame(cpuFrame, width=460, height=80, corner_radius=15, fg_color="#FFFFFF")
cpu_table.pack(padx=10, pady=10)
cpu_table.grid_propagate(False)

# Configure 4 columns: Job #, Time, Average WT, Average TAT
for col in range(4):
    cpu_table.grid_columnconfigure(col, weight=1)
for row in range(2):
    cpu_table.grid_rowconfigure(row, weight=1)

header_job     = tk.Label(cpu_table, text="Job #",      bg="#FFFFFF", font=("Arial", 10, "bold"))
header_time    = tk.Label(cpu_table, text="Time",       bg="#FFFFFF", font=("Arial", 10, "bold"))
header_avg_wt  = tk.Label(cpu_table, text="Average WT", bg="#FFFFFF", font=("Arial", 10, "bold"))
header_avg_tat = tk.Label(cpu_table, text="Average TAT",bg="#FFFFFF", font=("Arial", 10, "bold"))

header_job.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
header_time.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
header_avg_wt.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
header_avg_tat.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

value_job     = tk.Label(cpu_table, text="0", bg="#FFFFFF", font=("Arial", 10))
value_time    = tk.Label(cpu_table, text="0", bg="#FFFFFF", font=("Arial", 10))
value_avg_wt  = tk.Label(cpu_table, text="0", bg="#FFFFFF", font=("Arial", 10))
value_avg_tat = tk.Label(cpu_table, text="0", bg="#FFFFFF", font=("Arial", 10))

value_job.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
value_time.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
value_avg_wt.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
value_avg_tat.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")


# Queue Table (Ready Queue Display)

queueFrame = ctk.CTkFrame(root, width=480, height=100, corner_radius=15, fg_color="#028174")
queueFrame.place(x=500, y=425)

queue_table = ctk.CTkFrame(queueFrame, width=460, height=80, corner_radius=15, fg_color="#FFFFFF")
queue_table.pack(padx=10, pady=10)
queue_table.grid_propagate(False)

queue_label = tk.Label(queue_table, text="Ready Queue: ", bg="#FFFFFF", font=("Arial", 10))
queue_label.place(relx=0.5, rely=0.5, anchor="center")


# Buttons: Simulate, Generate Data, Pause, Reset

button_frame = ctk.CTkFrame(root, fg_color="transparent")
button_frame.place(x=200, y=625)

for i in range(4):
    button_frame.grid_columnconfigure(i, weight=1)

simulate_btn = ctk.CTkButton(button_frame, text="Simulate", command=simulate, state="disabled")
generate_btn = ctk.CTkButton(button_frame, text="Generate Data", command=generate_data)
pause_btn    = ctk.CTkButton(button_frame, text="Pause", command=pause, state="disabled")
reset_btn    = ctk.CTkButton(button_frame, text="Reset", command=reset)

simulate_btn.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
generate_btn.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
pause_btn.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
reset_btn.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

root.mainloop()
