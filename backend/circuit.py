"""Connectivity checks for one resistor and one LED on a 30-row breadboard.

No power rails are inferred. A-E and F-J are separate five-hole strips per row.
This is a topology checker, not an electrical simulator or photo classifier.
"""
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class Component(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,19}$")
    kind: Literal["resistor", "led", "wire"]
    pins: list[str] = Field(min_length=2, max_length=2)

    @field_validator("pins")
    @classmethod
    def valid_pins(cls, pins):
        return [validate_hole(pin) for pin in pins]


def validate_hole(hole: str) -> str:
    import re
    hole = hole.strip().upper()
    if not re.fullmatch(r"[A-J]([1-9]|[12][0-9]|30)", hole):
        raise ValueError("Use a hole from A1 to J30; power rails are not supported.")
    return hole


class Circuit(BaseModel):
    positive: str
    negative: str
    components: list[Component] = Field(max_length=30)

    @field_validator("positive", "negative")
    @classmethod
    def valid_supply(cls, value):
        return validate_hole(value)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [c.id for c in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("Component IDs must be unique.")
        return self


def strip(hole):
    return ("L" if hole[0] <= "E" else "R") + hole[1:]


def check(circuit: Circuit) -> dict:
    parent = {}

    def root(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = root(parent[node])
        return parent[node]

    def merge(a, b):
        parent[root(strip(a))] = root(strip(b))

    for c in circuit.components:
        if c.kind == "wire":
            merge(*c.pins)

    def connected(a, b):
        return root(strip(a)) == root(strip(b))

    findings = []

    def fault(code, title, detail, holes):
        findings.append(dict(code=code, title=title, detail=detail, holes=holes))

    if connected(circuit.positive, circuit.negative):
        fault("supply_short", "Supply terminals are shorted",
              "The marked positive and negative terminals share a conductive path. Remove the bridging connection before powering the circuit.",
              [circuit.positive, circuit.negative])
    resistors = [c for c in circuit.components if c.kind == "resistor"]
    leds = [c for c in circuit.components if c.kind == "led"]
    if len(resistors) != 1 or len(leds) != 1:
        fault("unsupported_parts", "This check needs one resistor and one LED",
              "Use one series resistor, one LED, and any required jumper wires. Other circuit types are not supported yet.", [])
    else:
        r, led = resistors[0], leds[0]
        a, k = led.pins
        for c in [r, led]:
            if connected(*c.pins):
                fault("component_bypassed", f"{c.id} is bypassed",
                      f"Both terminals of {c.id} share a conductive strip or wire path. Its two terminals need separate electrical nodes.", c.pins)

        def candidates(anode, cathode):
            options = []
            for p, q in [r.pins, r.pins[::-1]]:
                options.append([(circuit.positive, p), (q, anode), (cathode, circuit.negative)])
                options.append([(circuit.positive, anode), (cathode, p), (q, circuit.negative)])
            return options

        def missing(option):
            return [(x, y) for x, y in option if not connected(x, y)]

        if not findings:
            forward = candidates(a, k)
            if not any(not missing(option) for option in forward):
                if any(not missing(option) for option in candidates(k, a)):
                    fault("led_reversed", "LED polarity is reversed",
                          f"Swap {led.id}'s anode and cathode. Pin 1 must be the anode and pin 2 the cathode; confirm their identity on the physical LED.", [a, k])
                else:
                    best = min(forward, key=lambda option: len(missing(option)))
                    for x, y in missing(best):
                        fault("open_connection", "A series connection is missing",
                              f"There is no conductive connection between {x} and {y}. One possible repair is to join these nodes; check the reference before moving a wire.", [x, y])
    return {
        "status": "issues" if findings else "topology_pass",
        "findings": findings,
        "basis": "User-confirmed connections; no photo inference is used in this check.",
        "scope": "Checks connectivity and marked LED polarity only. Does not verify resistance, voltage, actual LED polarity, hidden contacts, or damaged parts.",
        "nets": {f"{col}{row}": root(strip(f"{col}{row}")) for col in "ABCDEFGHIJ" for row in range(1, 31)},
    }
