#!/usr/bin/env python3
"""Swap PID values in printer.cfg for hotend changes.

Reads the target hotend from save_variables (variables.cfg),
looks up the PID values, and rewrites the [extruder] PID block
in printer.cfg so only the selected hotend's PID is uncommented.

Usage: python3 swap_hotend_pid.py
  Reads current_hotend from ~/printer_data/config/variables.cfg
  Rewrites PID blocks in ~/printer_data/config/printer.cfg
"""
import re
import sys
import ast

CONFIG = "/home/pi/printer_data/config/printer.cfg"
VARIABLES = "/home/pi/printer_data/config/variables.cfg"

# PID blocks as they appear in printer.cfg (label → config lines)
# These must match the comment labels in your printer.cfg exactly
PID_BLOCKS = {
    "dragon_hf": {
        "label": "PID VALUES Dragon HF",
        "kp": 27.020, "ki": 1.857, "kd": 98.288
    },
    "raptor": {
        "label": "PID VALUES Raptor Protoprint",
        "kp": 48.060, "ki": 10.335, "kd": 55.872
    },
    "rapido_std": {
        "label": "PID VALUES Rapido",
        "kp": 19.024, "ki": 1.379, "kd": 65.636
    },
    "rapido_uhf": {
        "label": "PID VALUES Rapido UHF",
        "kp": 22.856, "ki": 1.656, "kd": 78.856
    },
}


def read_target_hotend():
    """Read current_hotend from variables.cfg."""
    with open(VARIABLES, "r") as f:
        for line in f:
            if line.strip().startswith("current_hotend"):
                # Format: current_hotend = 'dragon_hf'
                val = line.split("=", 1)[1].strip()
                return ast.literal_eval(val)
    return None


def swap_pid(target):
    """Rewrite printer.cfg PID blocks: uncomment target, comment others."""
    with open(CONFIG, "r") as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line is a PID label comment
        # Match longest label first to avoid "Rapido" matching "Rapido UHF"
        matched_hotend = None
        stripped_line = line.lstrip("#").strip()
        for hotend_id, block in sorted(
            PID_BLOCKS.items(), key=lambda x: len(x[1]["label"]), reverse=True
        ):
            if stripped_line == block["label"]:
                matched_hotend = hotend_id
                break

        if matched_hotend is not None:
            # This is a PID block header — rewrite the next 3 lines (control, kp, ki, kd)
            b = PID_BLOCKS[matched_hotend]
            if matched_hotend == target:
                # Active: uncommented label + uncommented values
                new_lines.append(f"# {b['label']}\n")
                new_lines.append(f"control = pid\n")
                new_lines.append(f"pid_kp = {b['kp']}\n")
                new_lines.append(f"pid_ki = {b['ki']}\n")
                new_lines.append(f"pid_kd = {b['kd']}\n")
            else:
                # Inactive: commented label + commented values
                new_lines.append(f"## {b['label']}\n")
                new_lines.append(f"# control = pid\n")
                new_lines.append(f"# pid_kp = {b['kp']}\n")
                new_lines.append(f"# pid_ki = {b['ki']}\n")
                new_lines.append(f"# pid_kd = {b['kd']}\n")

            # Skip original PID value lines (3-4 lines after header)
            i += 1
            while i < len(lines):
                stripped = lines[i].strip()
                # Skip lines that are pid values or control lines (commented or not)
                if stripped == "" or any(
                    stripped.lstrip("#").strip().startswith(k)
                    for k in ["control", "pid_kp", "pid_ki", "pid_kd"]
                ):
                    i += 1
                else:
                    break
            # Add blank line separator
            new_lines.append("\n")
            continue

        new_lines.append(line)
        i += 1

    with open(CONFIG, "w") as f:
        f.writelines(new_lines)

    print(f"PID swapped to: {target} (kp={PID_BLOCKS[target]['kp']})")


if __name__ == "__main__":
    target = read_target_hotend()
    if target is None:
        print("ERROR: Could not read current_hotend from variables.cfg", file=sys.stderr)
        sys.exit(1)
    if target not in PID_BLOCKS:
        print(f"ERROR: Unknown hotend '{target}'", file=sys.stderr)
        sys.exit(1)
    swap_pid(target)
