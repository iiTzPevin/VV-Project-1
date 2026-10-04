"""STEP 1 -- the skeleton: components, hierarchy, and who runs when.

No bus traffic yet. Every component announces its phases, and the log IS the
lesson: build_phase walks DOWN the tree (parents create children), then
connect_phase walks back UP (you cannot connect a port on a component that
does not exist yet), then every run_phase starts at once, and simulated time
passes only there. The schedule is fixed; your Week 4 testbench had the same
order -- enforced by you remembering it.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from pyuvm import uvm_component, uvm_agent, uvm_env, uvm_test, uvm_root

from demo_common import announce


class SkelDriver(uvm_component):
    def build_phase(self):
        announce(self, "build_phase")

    def connect_phase(self):
        announce(self, "connect_phase")

    async def run_phase(self):
        announce(self, "run_phase", "(would drive the bus here)")


class SkelMonitor(uvm_component):
    def build_phase(self):
        announce(self, "build_phase")

    def connect_phase(self):
        announce(self, "connect_phase")

    async def run_phase(self):
        announce(self, "run_phase", "(would watch the bus here)")


class SkelAgent(uvm_agent):
    def build_phase(self):
        announce(self, "build_phase", "-> creating driver, monitor")
        self.driver = SkelDriver("driver", self)
        self.monitor = SkelMonitor("monitor", self)

    def connect_phase(self):
        announce(self, "connect_phase", "(driver/monitor already connected)")


class SkelEnv(uvm_env):
    def build_phase(self):
        announce(self, "build_phase", "-> creating agent")
        self.agent = SkelAgent("agent", self)

    def connect_phase(self):
        announce(self, "connect_phase")


class PhaseTest(uvm_test):
    def build_phase(self):
        announce(self, "build_phase", "-> creating env")
        self.env = SkelEnv("env", self)

    def connect_phase(self):
        announce(self, "connect_phase")

    async def run_phase(self):
        self.raise_objection()               # hold the run phase open
        announce(self, "run_phase", "(sim time can pass only here)")
        await Timer(20, units="ns")
        self.drop_objection()

    def report_phase(self):
        announce(self, "report_phase", "(after run: tally and verdict)")


@cocotb.test()
async def test_phases(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await uvm_root().run_test("PhaseTest")
