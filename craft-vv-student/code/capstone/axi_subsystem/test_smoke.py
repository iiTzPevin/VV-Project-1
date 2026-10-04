"""SMOKE test -- AXI-ish interconnect subsystem (Track 2).

Brings up the 2-master round-robin arbiter + address-mapped bus + two scratch
register peripherals + the FWFT FIFO. Checks:
  * round-robin arbitration from reset under 2-master contention;
  * REG0 (via master 0) and REG1 (via master 1) write/read-back;
  * FIFO push/pop through the bus -- FWFT order + status(count/full/empty),
    scoreboarded against the golden FifoModel.

Single-cycle bus: a transaction is granted and completes in one clock. Inputs
are driven on the falling edge; the response is sampled mid-cycle; writes/pushes/
pops commit on the rising edge. This is a bring-up test, not the full suite.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from models.fifo_model import FifoModel

DW = 32
FIFO_DEPTH = 8
REG0_BASE = 0x0000
REG1_BASE = 0x1000
FIFO_DATA = 0x2000
FIFO_STAT = 0x2004


def _drive(dut, m, req, we=0, addr=0, wdata=0):
    if m == 0:
        dut.m0_req.value = req; dut.m0_we.value = we
        dut.m0_addr.value = addr; dut.m0_wdata.value = wdata
    else:
        dut.m1_req.value = req; dut.m1_we.value = we
        dut.m1_addr.value = addr; dut.m1_wdata.value = wdata


async def _idle(dut):
    _drive(dut, 0, 0); _drive(dut, 1, 0)


async def txn(dut, m, we, addr, wdata=0):
    """One single-master transaction. Returns (gnt, rvalid, rdata).

    rdata is resolved only for reads (we==0); on a write it is don't-care (the
    read-data bus can legitimately carry X, e.g. the FWFT head of an empty FIFO).
    """
    await FallingEdge(dut.clk)
    _drive(dut, m, 1, we, addr, wdata)
    _drive(dut, 1 - m, 0)
    await Timer(1, units="ns")                 # settle combinational grant/read
    gnt_s = dut.m0_gnt if m == 0 else dut.m1_gnt
    rv_s = dut.m0_rvalid if m == 0 else dut.m1_rvalid
    rd_s = dut.m0_rdata if m == 0 else dut.m1_rdata
    gnt, rvalid = int(gnt_s.value), int(rv_s.value)
    rdata = int(rd_s.value) if we == 0 else None
    await RisingEdge(dut.clk)                   # commit write/push/pop
    _drive(dut, m, 0)
    return gnt, rvalid, rdata


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await _idle(dut)
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


@cocotb.test()
async def test_arbitration(dut):
    """Round-robin: from reset, continuous 2-master contention alternates m1,m0,..."""
    await reset(dut)
    granted = []
    for _ in range(6):
        await FallingEdge(dut.clk)
        # both masters request (distinct scratch-reg writes)
        _drive(dut, 0, 1, we=1, addr=REG0_BASE + 0x0, wdata=0xA0A0A0A0)
        _drive(dut, 1, 1, we=1, addr=REG1_BASE + 0x0, wdata=0xB1B1B1B1)
        await Timer(1, units="ns")
        g0, g1 = int(dut.m0_gnt.value), int(dut.m1_gnt.value)
        assert g0 + g1 == 1, f"exactly one grant expected, got g0={g0} g1={g1}"
        # only the granted master is rvalid
        assert int(dut.m0_rvalid.value) == g0 and int(dut.m1_rvalid.value) == g1
        granted.append(0 if g0 else 1)
        await RisingEdge(dut.clk)
    await _idle(dut)
    assert granted == [1, 0, 1, 0, 1, 0], f"round-robin order wrong: {granted}"


@cocotb.test()
async def test_registers(dut):
    """Both scratch-register peripherals: write then read back, per master."""
    await reset(dut)
    # master 0 -> REG0[0..3]
    vals0 = [0xDEADBEEF, 0x00C0FFEE, 0x12345678, 0xFFFFFFFF]
    for i, v in enumerate(vals0):
        g, _, _ = await txn(dut, 0, we=1, addr=REG0_BASE + 4 * i, wdata=v)
        assert g == 1
    for i, v in enumerate(vals0):
        g, rv, rd = await txn(dut, 0, we=0, addr=REG0_BASE + 4 * i)
        assert g == 1 and rv == 1 and rd == v, f"REG0[{i}]={rd:#x} != {v:#x}"
    # master 1 -> REG1[0..3]
    vals1 = [0xCAFEBABE, 0x8BADF00D, 0x0BADCAFE, 0x1BADB002]
    for i, v in enumerate(vals1):
        g, _, _ = await txn(dut, 1, we=1, addr=REG1_BASE + 4 * i, wdata=v)
        assert g == 1
    for i, v in enumerate(vals1):
        g, rv, rd = await txn(dut, 1, we=0, addr=REG1_BASE + 4 * i)
        assert g == 1 and rv == 1 and rd == v, f"REG1[{i}]={rd:#x} != {v:#x}"
    # cross-check: REG0 and REG1 are independent (no aliasing)
    _, _, rd = await txn(dut, 0, we=0, addr=REG0_BASE + 0)
    assert rd == vals0[0], "REG0[0] clobbered by REG1 writes (aliasing)"


def _status_word(model):
    full = 1 if model.full else 0
    empty = 1 if model.empty else 0
    return ((model.count & 0xF) << 2) | (full << 1) | empty


@cocotb.test()
async def test_fifo(dut):
    """FIFO peripheral through the bus: push/pop FWFT order + status register."""
    await reset(dut)
    model = FifoModel(DW, FIFO_DEPTH)
    model.reset()

    payload = [0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555]
    # push
    for v in payload:
        g, _, _ = await txn(dut, 0, we=1, addr=FIFO_DATA, wdata=v)
        assert g == 1
        model.step(wr_en=1, wr_data=v, rd_en=0)
    # status after pushes
    _, rv, st = await txn(dut, 0, we=0, addr=FIFO_STAT)
    assert rv == 1 and st == _status_word(model), \
        f"status {st:#x} != model {_status_word(model):#x} (count={model.count})"
    # pop everything, checking FWFT order
    for _ in range(len(payload)):
        want = model.head
        _, rv, rd = await txn(dut, 1, we=0, addr=FIFO_DATA)     # master 1 pops
        assert rv == 1 and rd == want, f"FIFO pop {rd:#x} != head {want:#x}"
        model.step(wr_en=0, wr_data=0, rd_en=1)
    # status after drain: empty
    _, _, st = await txn(dut, 0, we=0, addr=FIFO_STAT)
    assert st == _status_word(model), f"drained status {st:#x} != {_status_word(model):#x}"
    assert (st & 1) == 1, "empty bit should be set after draining"
    dut._log.info("AXI subsystem smoke PASS: arbiter + regs + FIFO all correct.")
