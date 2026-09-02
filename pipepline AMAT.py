STAGES = ["IF", "ID", "EX", "MEM", "WB"]


class Instr:
    def __init__(self, text, dest=None, src1=None, src2=None, is_load=False, is_branch=False):
        self.text = text
        self.dest = dest
        self.src1 = src1
        self.src2 = src2
        self.is_load = is_load
        self.is_branch = is_branch

    def reads(self):
        return {r for r in (self.src1, self.src2) if r is not None}


# The 5-instruction sequence from Section 5.2 of the report
PROGRAM = [
    Instr("I1: ADD  R1, R2, R3",   dest="R1", src1="R2", src2="R3"),
    Instr("I2: SUB  R4, R1, R5",   dest="R4", src1="R1", src2="R5"),
    Instr("I3: LOAD R6, [R4+0]",   dest="R6", src1="R4", is_load=True),
    Instr("I4: BEQ  R6, R7, L1",           src1="R6", src2="R7", is_branch=True),
    Instr("I5: ADD  R8, R9, R10",  dest="R8", src1="R9", src2="R10"),
]


def depends(consumer, producer):
    return producer.dest is not None and producer.dest in consumer.reads()


def simulate(program, forwarding):
    n = len(program)
    state = {s: None for s in STAGES}   # stage -> instr index or None
    state["IF"] = 0 if n > 0 else None  # instruction 0 is fetched starting cycle 1
    next_fetch = 1
    cycle = 0
    finished = 0
    timeline = {i: {} for i in range(n)}
    stall_cycles = 0

    while finished < n and cycle < 60:
        cycle += 1
        # record occupancy for this cycle from the state as it stands entering the cycle
        for stage, idx in state.items():
            if idx is not None:
                timeline[idx][cycle] = stage

        new_state = dict(state)

        # retire whoever is currently in WB
        if state["WB"] is not None:
            finished += 1

        # decide stall for instruction currently in ID
        stall = False
        if state["ID"] is not None:
            i = program[state["ID"]]
            for stage_ahead in ("EX", "MEM", "WB"):
                p_idx = state[stage_ahead]
                if p_idx is not None and depends(i, program[p_idx]):
                    if forwarding:
                        if stage_ahead == "EX" and program[p_idx].is_load:
                            stall = True   # load-use hazard: 1 stall even with forwarding
                        # EX/EX forward (non-load) and MEM/EX forward: no stall
                    else:
                        stall = True      # no forwarding hardware at all: always stall

        new_state["WB"] = state["MEM"]
        new_state["MEM"] = state["EX"]
        if stall:
            new_state["EX"] = None       # bubble
            new_state["ID"] = state["ID"]  # instruction held in ID
            new_state["IF"] = state["IF"]  # fetch holds
            stall_cycles += 1
        else:
            new_state["EX"] = state["ID"]
            new_state["ID"] = state["IF"]
            if next_fetch < n:
                new_state["IF"] = next_fetch
                next_fetch += 1
            else:
                new_state["IF"] = None

        state = new_state

    total_cycles = cycle
    return timeline, total_cycles, stall_cycles


def print_timeline(title, timeline, total_cycles, program):
    print(f"\n=== {title} ===")
    header = "Instr".ljust(24) + "".join(f"{c:>5}" for c in range(1, total_cycles + 1))
    print(header)
    for idx, instr in enumerate(program):
        row = instr.text.ljust(24)
        for c in range(1, total_cycles + 1):
            row += f"{timeline[idx].get(c, ''):>5}"
        print(row)


def report_cpi(name, program, forwarding):
    timeline, total_cycles, stalls = simulate(program, forwarding)
    cpi = total_cycles / len(program)
    print_timeline(name, timeline, total_cycles, program)
    print(f"Stall cycles inserted : {stalls}")
    print(f"Total cycles          : {total_cycles}")
    print(f"CPI = cycles / N      : {total_cycles}/{len(program)} = {cpi:.2f}")
    return total_cycles, stalls, cpi


if __name__ == "__main__":
    print("PIPELINE HAZARD SIMULATION — Section 5.2 instruction sequence")
    print("=" * 70)
    c_u, s_u, cpi_u = report_cpi("WITHOUT hazard mitigation (no forwarding)", PROGRAM, forwarding=False)
    c_m, s_m, cpi_m = report_cpi("WITH hazard mitigation (EX/EX + MEM/EX forwarding)", PROGRAM, forwarding=True)
    print("\n" + "=" * 70)
    print("SUMMARY")
    print(f"  Unmitigated : {c_u} cycles, {s_u} stalls, CPI = {cpi_u:.2f}")
    print(f"  Mitigated   : {c_m} cycles, {s_m} stalls, CPI = {cpi_m:.2f}")
    print(f"  CPI reduction: {(1 - cpi_m / cpi_u) * 100:.1f}%")
def amat(levels, mem_time):
    """
    levels: list of (hit_time, local_miss_rate) from L1 to the last cache level.
    mem_time: main-memory access time in cycles.
    Returns AMAT in cycles, evaluated from the last level back to L1.
    """
    t = mem_time
    for hit_time, miss_rate in reversed(levels):
        t = hit_time + miss_rate * t
    return t


def dram_reference_fraction(levels):
    """Fraction of all memory references that reach DRAM = product of local miss rates."""
    frac = 1.0
    for _, miss_rate in levels:
        frac *= miss_rate
    return frac


def throughput_row(name, cpi_pipeline, cache_levels, mem_time, ls_fraction, clock_ghz):
    a = amat(cache_levels, mem_time)
    l1_hit_time = cache_levels[0][0]
    cpi_total = cpi_pipeline + ls_fraction * (a - l1_hit_time)
    ipc = 1 / cpi_total
    throughput = ipc * clock_ghz
    return {
        "name": name, "cpi_pipeline": cpi_pipeline, "amat": a,
        "cpi_total": cpi_total, "ipc": ipc, "throughput_gips": throughput,
    }


if __name__ == "__main__":
    L1 = (1, 0.05)
    L2 = (10, 0.20)
    L3 = (30, 0.30)
    MEM_TIME = 200
    LS_FRACTION = 0.30
    CLOCK_GHZ = 2.0

    print("AMAT — Section 5.4")
    print("=" * 60)
    three_level = [L1, L2, L3]
    two_level = [L1, L2]

    a3 = amat(three_level, MEM_TIME)
    a2 = amat(two_level, MEM_TIME)
    print(f"AMAT (3-level, L1+L2+L3) = {a3:.2f} cycles")
    print(f"AMAT (2-level, L1+L2)    = {a2:.2f} cycles")
    print(f"Reduction from adding L3 = {(1 - a3 / a2) * 100:.1f}%")

    print("\nDRAM reference fraction (bandwidth demand) — Section 10")
    print("=" * 60)
    f3 = dram_reference_fraction(three_level)
    f2 = dram_reference_fraction(two_level)
    print(f"3-level design: {f3*100:.2f}% of references reach DRAM")
    print(f"2-level design: {f2*100:.2f}% of references reach DRAM")
    print(f"DRAM traffic reduction from adding L3: {f2 / f3:.1f}x fewer DRAM references")

    print("\nThroughput comparison across design alternatives — Section 10")
    print("=" * 60)
    rows = [
        throughput_row("A: Scalar + 2-level cache", 2.00, two_level, MEM_TIME, LS_FRACTION, CLOCK_GHZ),
        throughput_row("B: Scalar + 3-level cache", 2.00, three_level, MEM_TIME, LS_FRACTION, CLOCK_GHZ),
        throughput_row("C: 2-way superscalar + 3-level cache", 0.70, three_level, MEM_TIME, LS_FRACTION, CLOCK_GHZ),
    ]
    hdr = f'{"Design":38}{"CPI_pipe":>9}{"AMAT":>7}{"CPI_tot":>9}{"IPC":>7}{"GIPS":>8}'
    print(hdr)
    for r in rows:
        print(f'{r["name"]:38}{r["cpi_pipeline"]:>9.2f}{r["amat"]:>7.2f}'
              f'{r["cpi_total"]:>9.2f}{r["ipc"]:>7.2f}{r["throughput_gips"]:>8.2f}')

    gain_b_over_a = rows[1]["throughput_gips"] / rows[0]["throughput_gips"] - 1
    gain_c_over_a = rows[2]["throughput_gips"] / rows[0]["throughput_gips"] - 1
    gain_c_over_b = rows[2]["throughput_gips"] / rows[1]["throughput_gips"] - 1
    print(f"\nB vs A (adding L3):                {gain_b_over_a*100:+.1f}% throughput")
    print(f"C vs B (adding 2-way superscalar):  {gain_c_over_b*100:+.1f}% throughput")
    print(f"C vs A (both improvements):         {gain_c_over_a*100:+.1f}% throughput")

