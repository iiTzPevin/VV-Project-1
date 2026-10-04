"""Golden reference model for the CRAFT axil_regfile (dut/axil_regfile.sv).

Mirrors reset values and *every* access policy the RTL enforces:
  - CTRL / SCRATCH : plain RW
  - STATUS         : RO  (writes ignored; reads a fixed pattern)
  - INTR           : W1C (write-1-to-clear); hardware sets bit0 on a
                     security violation (a write to SECURE while locked)
  - LOCK           : RW  (bit0 = lock enable)
  - SECURE         : locked-RW (writable only while LOCK.bit0 == 0)
  - other addrs    : read 0, writes ignored

Usage mirrors a register block: `write(addr, data)` advances state exactly as
the DUT would on a bus write; `read(addr)` returns what the DUT will present on
rdata for that address given the current state.  The scoreboard replays the
observed transaction stream through this model and checks every read.
"""


class RegfileModel:
    # ---- address map ----
    ADDR_CTRL = 0x0
    ADDR_STATUS = 0x1
    ADDR_SCRATCH = 0x2
    ADDR_INTR = 0x3
    ADDR_LOCK = 0x4
    ADDR_SECURE = 0x5

    STATUS_VAL = 0x5A5A0F0F      # fixed RO read pattern (also STATUS reset value)
    MASK = 0xFFFFFFFF

    # reset values, by address (unmapped -> read 0)
    RESET = {
        ADDR_CTRL: 0x00000000,
        ADDR_STATUS: STATUS_VAL,
        ADDR_SCRATCH: 0x00000000,
        ADDR_INTR: 0x00000000,
        ADDR_LOCK: 0x00000000,
        ADDR_SECURE: 0x00000000,
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.ctrl = self.RESET[self.ADDR_CTRL]
        self.status = self.RESET[self.ADDR_STATUS]
        self.scratch = self.RESET[self.ADDR_SCRATCH]
        self.intr = self.RESET[self.ADDR_INTR]
        self.lock = self.RESET[self.ADDR_LOCK]
        self.secure = self.RESET[self.ADDR_SECURE]

    @property
    def locked(self):
        return bool(self.lock & 0x1)

    def write(self, addr, data):
        """Apply a bus write exactly as the DUT would (policies enforced)."""
        addr &= 0xF
        data &= self.MASK
        if addr == self.ADDR_CTRL:
            self.ctrl = data                       # RW
        elif addr == self.ADDR_STATUS:
            pass                                   # RO: writes ignored
        elif addr == self.ADDR_SCRATCH:
            self.scratch = data                    # RW
        elif addr == self.ADDR_INTR:
            self.intr = self.intr & (~data & self.MASK)   # W1C
        elif addr == self.ADDR_LOCK:
            self.lock = data                       # RW
        elif addr == self.ADDR_SECURE:
            if not self.locked:
                self.secure = data                 # locked-RW: only while unlocked
            else:
                self.intr |= 0x1                   # security violation -> hw sets INTR bit0
        # unmapped: writes ignored

    def read(self, addr):
        """Return the value the DUT presents on rdata for this address."""
        addr &= 0xF
        if addr == self.ADDR_CTRL:
            return self.ctrl
        elif addr == self.ADDR_STATUS:
            return self.status
        elif addr == self.ADDR_SCRATCH:
            return self.scratch
        elif addr == self.ADDR_INTR:
            return self.intr
        elif addr == self.ADDR_LOCK:
            return self.lock
        elif addr == self.ADDR_SECURE:
            return self.secure
        return 0x00000000                          # unmapped reads 0
