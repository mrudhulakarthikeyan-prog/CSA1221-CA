"""
CSA1221 - COMPUTER ARCHITECTURE
Design and Performance Analysis of a Pipelined Processor
with a Multi-Level Cache Memory System

Single-file implementation covering all 10 deliverables.
Run this file directly in Python IDLE (or `python CSA1221_Processor.py`)
and copy the console output into the Sample Output box of each
deliverable in the report.
"""


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ======================================================================
# DELIVERABLE 1: Register-Transfer Notation and Multiple-Bus Datapath
# ======================================================================

class RegisterFile:
    def __init__(self):
        self.regs = {}

    def read(self, reg):
        return self.regs.get(reg, 0)

    def write(self, reg, value):
        self.regs[reg] = value


class Memory:
    def __init__(self):
        self.mem = {}

    def read(self, addr):
        return self.mem.get(addr, 0)

    def write(self, addr, value):
        self.mem[addr] = value


def multi_bus_execute(instr, rf, mem):
    op = instr[0]

    if op == "ADD":
        _, rd, rs, rt = instr
        busA = rf.read(rs)
        busB = rf.read(rt)
        alu_out = busA + busB
        rf.write(rd, alu_out)
        print(f"ADD : {rd} <- {rs} + {rt} = {alu_out}")

    elif op == "LOAD":
        _, rt, offset, rs = instr
        busA = rf.read(rs)
        ea = busA + offset
        value = mem.read(ea)
        rf.write(rt, value)
        print(f"LOAD : EA <- {busA} + {offset} = {ea}; {rt} <- Memory[{ea}] = {value}")

    elif op == "STORE":
        _, rt, offset, rs = instr
        busA = rf.read(rs)
        busB = rf.read(rt)
        ea = busA + offset
        mem.write(ea, busB)
        print(f"STORE : EA <- {busA} + {offset} = {ea}; Memory[{ea}] <- {busB}")

    elif op == "BEQ":
        _, rs, rt, label = instr
        busA = rf.read(rs)
        busB = rf.read(rt)
        alu_out = busA - busB
        taken = "branch target selected" if alu_out == 0 else "branch not taken"
        print(f"BEQ : {rs} - {rt} = {alu_out}; {taken}")


def deliverable_1():
    section("DELIVERABLE 1: Register-Transfer Notation and Multiple-Bus Datapath")
    rf = RegisterFile()
    mem = Memory()

    print("MULTIPLE-BUS DATAPATH EXECUTION")
    print("Bus A -> source operand 1")
    print("Bus B -> source operand 2")
    print("ALU   -> arithmetic / address / comparison")
    print("Bus C -> result written back to register file")
    print()

    # ADD R3, R1, R2   (R1=12, R2=8)
    rf.write("R1", 12)
    rf.write("R2", 8)
    multi_bus_execute(("ADD", "R3", "R1", "R2"), rf, mem)

    # LOAD R5, 16(R1)  (R1=1000, Memory[1016]=45)
    rf.write("R1", 1000)
    mem.write(1016, 45)
    multi_bus_execute(("LOAD", "R5", 16, "R1"), rf, mem)

    # STORE R4, 20(R1) (R1=1000, R4=90)
    rf.write("R4", 90)
    multi_bus_execute(("STORE", "R4", 20, "R1"), rf, mem)

    # BEQ R1, R2, LABEL (R1=R2)
    rf.write("R2", 1000)
    multi_bus_execute(("BEQ", "R1", "R2", "LABEL"), rf, mem)


# ======================================================================
# DELIVERABLE 2: Instruction-Level Datapath Operation Analysis
# ======================================================================

def process_instr(instr, rf, mem):
    op = instr[0]
    if op == "LOAD":
        _, rd, offset, rs = instr
        ea = rf.read(rs) + offset
        mdr = mem.read(ea)
        rf.write(rd, mdr)
        print(f"LOAD {rd},{offset}({rs})   EA={rs}+{offset}={ea}; MDR=Memory[{ea}]={mdr}; {rd}={mdr}")
    elif op == "ADD":
        _, rd, rs, rt = instr
        alu = rf.read(rs) + rf.read(rt)
        rf.write(rd, alu)
        print(f"ADD {rd},{rs},{rt}        ALUout={rs}+{rt}={alu}; {rd}={alu}")
    elif op == "STORE":
        _, rs2, offset, rs = instr
        ea = rf.read(rs) + offset
        mem.write(ea, rf.read(rs2))
        print(f"STORE {rs2},{offset}({rs})  EA={rs}+{offset}={ea}; Memory[{ea}]={rs2}")
    elif op == "BEQ":
        _, rs, rt, label = instr
        equal = rf.read(rs) == rf.read(rt)
        print(f"BEQ {rs},{rt},{label}   ALU compares {rs} and {rt}; PC updated={'yes' if equal else 'no'}")


def deliverable_2():
    section("DELIVERABLE 2: Instruction-Level Datapath Operation Analysis")
    rf = RegisterFile()
    rf.regs = {"R0": 0, "R1": 0, "R2": 0, "R3": 0, "R4": 5}
    mem = Memory()
    mem.write(0, 77)  # value stored at address R2 + 0, used by the LOAD

    print("Instruction Register Transfer / Main Resource")
    # Sequence: LOAD R1,0(R2) -> ADD R3,R1,R4 -> STORE R3,8(R2) -> BEQ R3,R0,EXIT
    process_instr(("LOAD", "R1", 0, "R2"), rf, mem)
    process_instr(("ADD", "R3", "R1", "R4"), rf, mem)
    process_instr(("STORE", "R3", 8, "R2"), rf, mem)
    process_instr(("BEQ", "R3", "R0", "EXIT"), rf, mem)


# ======================================================================
# DELIVERABLE 3: Five-Stage Pipeline Design
# ======================================================================

def build_pipeline_table(instrs, stages):
    table = {}
    for i, instr in enumerate(instrs):
        table[instr] = {}
        for j, stage in enumerate(stages):
            cycle = i + j + 1
            table[instr][cycle] = stage
    return table


def deliverable_3():
    section("DELIVERABLE 3: Five-Stage Pipeline Design")
    stages = ["IF", "ID", "EX", "MEM", "WB"]
    instructions = ["I1", "I2", "I3", "I4"]

    table = build_pipeline_table(instructions, stages)
    max_cycle = len(instructions) + len(stages) - 1

    header = "Cycle " + " ".join(f"{instr:>4}" for instr in instructions)
    print(header)
    for cycle in range(1, max_cycle + 1):
        row = [f"{cycle:<5}"]
        for instr in instructions:
            row.append(f"{table[instr].get(cycle, ''):>4}")
        print(" ".join(row))


# ======================================================================
# DELIVERABLE 4: Hazard Analysis and CPI With/Without Mitigation
# ======================================================================

def cpi_without_mitigation(base_cycles, data_hazard_stalls, control_hazard_penalty):
    total = base_cycles + data_hazard_stalls + control_hazard_penalty
    cpi = total / base_cycles
    return total, cpi


def cpi_with_mitigation(base_cycles, load_use_stalls, branches, mispred_rate, mispred_penalty):
    misprediction_cycles = branches * mispred_rate * mispred_penalty
    total = base_cycles + load_use_stalls + misprediction_cycles
    cpi = total / base_cycles
    return total, misprediction_cycles, cpi


def deliverable_4():
    section("DELIVERABLE 4: Hazard Analysis and CPI With/Without Mitigation")
    base_cycles = 100
    data_hazard_stalls = 45
    control_hazard_penalty = 40

    total_wo, cpi_wo = cpi_without_mitigation(base_cycles, data_hazard_stalls, control_hazard_penalty)
    print("CPI WITHOUT HAZARD MITIGATION")
    print(f"Base cycles = {base_cycles}")
    print(f"Data-hazard stall cycles (estimate) = {data_hazard_stalls}")
    print(f"Control-hazard penalty = {control_hazard_penalty}")
    print(f"Total cycles = {total_wo}")
    print(f"CPI = {total_wo} / {base_cycles} = {cpi_wo:.2f}")
    print()

    load_use_stalls = 10
    branches = 20
    mispred_rate = 0.10
    mispred_penalty = 2

    total_w, mispred_cycles, cpi_w = cpi_with_mitigation(
        base_cycles, load_use_stalls, branches, mispred_rate, mispred_penalty
    )
    print("CPI WITH FORWARDING + PREDICTION")
    print(f"Base cycles = {base_cycles}")
    print(f"Remaining load-use stalls = {load_use_stalls}")
    print(f"Misprediction penalty = {branches}*{mispred_rate}*{mispred_penalty} = {mispred_cycles}")
    print(f"Total cycles = {total_w}")
    print(f"CPI = {total_w} / {base_cycles} = {cpi_w:.2f}")


# ======================================================================
# DELIVERABLE 5: Two-Way Superscalar Processor Design
# ======================================================================

class Instruction:
    def __init__(self, op, dest, src1, src2, unit):
        self.op = op
        self.dest = dest
        self.src1 = src1
        self.src2 = src2
        self.unit = unit


def dispatch(instrs):
    print("2-WAY DISPATCH")
    for i in range(0, len(instrs), 2):
        pair = instrs[i:i + 2]
        for slot, instr in enumerate(pair):
            print(f"Slot {slot} -> {instr.unit} executes {instr.op} {instr.dest},{instr.src1},{instr.src2}")
    print("Cycle dispatch capacity: up to 2 instructions")
    print("Issue policy: operands ready + execution unit available")
    print("Commit policy: in program order using Reorder Buffer")


def deliverable_5():
    section("DELIVERABLE 5: Two-Way Superscalar Processor Design")
    instrs = [
        Instruction("ADD", "R3", "R1", "R2", "Integer ALU / Branch execution unit"),
        Instruction("LOAD", "R5", "R6", "0", "Load-Store execution unit"),
    ]
    dispatch(instrs)


# ======================================================================
# DELIVERABLE 6: Out-of-Order and Speculative Execution with Recovery
# ======================================================================

class ReorderBufferEntry:
    def __init__(self, instr, done=False):
        self.instr = instr
        self.done = done


def simulate_ooo(instrs, branch_correct):
    rob = [ReorderBufferEntry(i) for i in instrs]

    print("OUT-OF-ORDER EXAMPLE")
    for entry in rob:
        if entry.instr.startswith("LOAD"):
            print(f"{entry.instr} -> waiting for memory")
        elif entry.instr.startswith("ADD"):
            entry.done = True
            print(f"{entry.instr} -> executes early because operands are ready")
        elif entry.instr.startswith("BRANCH"):
            print(f"{entry.instr} -> predicted and executed speculatively")

    if not branch_correct:
        print()
        print("MISPREDICTION RECOVERY")
        print("1. Stop committing wrong-path younger instructions")
        print("2. Flush speculative pipeline/queue entries")
        print("3. Restore rename-map checkpoint")
        print("4. Set PC to correct branch target")
        print("5. Resume instruction fetch")
    else:
        print()
        print("Branch prediction correct: continue normal execution")


def deliverable_6():
    section("DELIVERABLE 6: Out-of-Order and Speculative Execution with Recovery")
    instrs = ["LOAD R1,0(R2)", "ADD R5,R6,R7", "BRANCH"]
    simulate_ooo(instrs, branch_correct=False)


# ======================================================================
# DELIVERABLE 7: Multi-Level Cache and Virtual Memory Design
# ======================================================================

cache_levels = [
    {"name": "L1 I-cache", "size_kb": 32, "assoc": 4, "hit_ns": 1, "policy": "Pseudo-LRU", "tech": "SRAM"},
    {"name": "L1 D-cache", "size_kb": 32, "assoc": 4, "hit_ns": 1, "policy": "Pseudo-LRU", "tech": "SRAM"},
    {"name": "L2 Unified", "size_kb": 512, "assoc": 8, "hit_ns": 5, "policy": "Pseudo-LRU", "tech": "SRAM"},
    {"name": "L3 Shared/Unified", "size_kb": 8192, "assoc": 16, "hit_ns": 20,
     "policy": "SRAM + capacity-oriented", "tech": "SRAM"},
]


def print_hierarchy(levels):
    print(f"{'Level':<20}{'Size':<10}{'Assoc':<8}{'Hit Time':<10}{'Replacement':<25}{'Technology'}")
    for lvl in levels:
        size = f"{lvl['size_kb']} KB" if lvl['size_kb'] < 1024 else f"{lvl['size_kb']//1024} MB"
        print(f"{lvl['name']:<20}{size:<10}{lvl['assoc']}-way{'':<3}{lvl['hit_ns']} ns{'':<5}"
              f"{lvl['policy']:<25}{lvl['tech']}")
    print(f"{'Main Memory':<20}{'8 GB':<10}{'-':<8}{'100 ns':<10}{'-':<25}DRAM")


def address_translation_flow():
    print()
    print("CPU -> L1 -> L2 -> L3 -> DRAM")
    print("        |")
    print("        v")
    print("   TLB / Page Table")
    print("Virtual address -> TLB translation -> Physical cache/memory access")


def deliverable_7():
    section("DELIVERABLE 7: Multi-Level Cache and Virtual Memory Design")
    print_hierarchy(cache_levels)
    address_translation_flow()


# ======================================================================
# DELIVERABLE 8: AMAT Calculation and Memory Technology Justification
# ======================================================================

def amat_three_level(l1_hit, l1_miss, l2_hit, l2_miss, l3_hit, l3_miss, dram_penalty):
    return l1_hit + l1_miss * (l2_hit + l2_miss * (l3_hit + l3_miss * dram_penalty))


def amat_two_level(l1_hit, l1_miss, l2_hit, l2_miss, dram_penalty):
    return l1_hit + l1_miss * (l2_hit + l2_miss * dram_penalty)


def deliverable_8():
    section("DELIVERABLE 8: AMAT Calculation and Memory Technology Justification")
    l1_hit, l1_miss = 1, 0.05
    l2_hit, l2_miss = 5, 0.10
    l3_hit, l3_miss = 20, 0.20
    dram_penalty = 100

    amat3 = amat_three_level(l1_hit, l1_miss, l2_hit, l2_miss, l3_hit, l3_miss, dram_penalty)
    print("3-LEVEL CACHE AMAT")
    print(f"AMAT = {l1_hit} + {l1_miss} x [{l2_hit} + {l2_miss} x ({l3_hit} + {l3_miss} x {dram_penalty})]")
    print(f"     = {amat3:.2f} ns")
    print()

    amat2 = amat_two_level(l1_hit, l1_miss, l2_hit, 0.10, dram_penalty)
    print("2-LEVEL ALTERNATIVE (assume L2 local miss rate = 10%)")
    print(f"AMAT = {l1_hit} + {l1_miss} x ({l2_hit} + 0.10 x {dram_penalty})")
    print(f"     = {amat2:.2f} ns")
    print()

    improvement = amat2 - amat3
    pct = (improvement / amat2) * 100
    print(f"Improvement with L3 = {amat2:.2f} - {amat3:.2f} = {improvement:.2f} ns "
          f"(~{pct:.1f}% lower AMAT)")


# ======================================================================
# DELIVERABLE 9: Bandwidth and Throughput Comparison
# ======================================================================

def scalar_throughput(clock_ghz, cpi):
    return clock_ghz / cpi


def superscalar_throughput(clock_ghz, ipc):
    return clock_ghz * ipc


def peak_bandwidth(clock_hz, bytes_per_transfer):
    return clock_hz * bytes_per_transfer


def deliverable_9():
    section("DELIVERABLE 9: Bandwidth and Throughput Comparison")
    clock_ghz = 2
    scalar_cpi = 1.14
    superscalar_ipc = 1.60
    cache_line_bytes = 64
    amat_2level = 1.75
    amat_3level = 1.45

    scalar_gips = scalar_throughput(clock_ghz, scalar_cpi)
    superscalar_gips = superscalar_throughput(clock_ghz, superscalar_ipc)
    bw = peak_bandwidth(clock_ghz * 1e9, cache_line_bytes)
    pct_higher = (superscalar_gips / scalar_gips - 1) * 100

    print(f"{'Alternative':<20}{'Performance Estimate':<38}{'Interpretation'}")
    print(f"{'Scalar 5-stage':<20}"
          f"{f'{clock_ghz} GHz / {scalar_cpi} = {scalar_gips:.2f} GIPS':<38}"
          f"{'Baseline throughput'}")
    print(f"{'2-way superscalar':<20}"
          f"{f'{clock_ghz} GHz x {superscalar_ipc} IPC = {superscalar_gips:.2f} GIPS':<38}"
          f"{f'~{pct_higher:.0f}% higher than scalar'}")
    print(f"{'2-level cache':<20}{f'AMAT = {amat_2level} ns':<38}{'Simpler, more DRAM exposure'}")
    print(f"{'3-level cache':<20}{f'AMAT = {amat_3level} ns':<38}{'Lower AMAT'}")
    print(f"{'L2 peak bandwidth':<20}{f'{bw/1e9:.0f} GB/s':<38}{'Theoretical interface peak'}")


# ======================================================================
# DELIVERABLE 10: Reflection, SDG 9 Relevance and Viva Readiness
# ======================================================================

deliverables_map = {
    1: "Register-transfer notation and multiple-bus datapath design",
    2: "Load, store, add and branch data movement analysis",
    3: "Five-stage pipeline design: IF, ID, EX, MEM and WB",
    4: "Data and control hazard identification with CPI comparison",
    5: "2-way superscalar dispatch and execution design",
    6: "Out-of-order, speculative execution and misprediction recovery",
    7: "L1/L2/L3 cache hierarchy and virtual memory design",
    8: "AMAT calculation and memory technology justification",
    9: "Bandwidth and throughput comparison of design alternatives",
    10: "Reflection, SDG 9 relevance, learning outcomes and viva readiness",
}

viva_questions = {
    "Why is a multiple-bus organization used?":
        "It allows simultaneous operand transfers and reduces bus conflicts.",
    "What is a RAW hazard?":
        "A Read After Write dependency where an instruction needs a value "
        "produced by an earlier instruction.",
    "Why is forwarding useful?":
        "It sends a produced result directly to a dependent stage without "
        "waiting for normal write-back.",
    "What is speculative execution?":
        "Executing instructions based on a prediction before the prediction "
        "is confirmed.",
    "How does a reorder buffer help?":
        "It allows out-of-order execution while committing results in "
        "program order.",
    "Why is SRAM used for L1?":
        "SRAM provides very low latency and does not require refresh.",
    "What is AMAT?":
        "Average Memory Access Time, combining hit time and expected "
        "miss penalties.",
    "Why add L3 cache?":
        "It can reduce costly main-memory accesses and lower AMAT for "
        "suitable workloads.",
}


def deliverable_10():
    section("DELIVERABLE 10: Reflection, SDG 9 Relevance and Viva Readiness")
    print("DELIVERABLE MAPPING")
    for num, desc in deliverables_map.items():
        print(f"{num:>2}. {desc}")

    print()
    print("VIVA QUESTIONS AND ANSWERS")
    for i, (q, a) in enumerate(viva_questions.items(), start=1):
        print(f"{i}. {q}")
        print(f"   {a}")


# ======================================================================
# MAIN: run all deliverables in sequence
# ======================================================================

if __name__ == "__main__":
    deliverable_1()
    deliverable_2()
    deliverable_3()
    deliverable_4()
    deliverable_5()
    deliverable_6()
    deliverable_7()
    deliverable_8()
    deliverable_9()
    deliverable_10()
