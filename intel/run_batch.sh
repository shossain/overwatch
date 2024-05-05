#!/usr/bin/env bash

export VIDEO="ukraine_tank_cut"
#CAPTION="person.human.soldier" python3 demo_inst.py
CAPTION="tank.vehicle.car" python3 demo_inst.py
CAPTION="smoke.fire" python3 demo_inst.py
# CAPTION="gun.weapon" python3 demo_inst.py

python3 stitch_results.py