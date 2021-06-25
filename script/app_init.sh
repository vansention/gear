#!/bin/bash


python solid_ctrl.py -f db.create_table
python solid_ctrl.py -f user_id.init
python solid_ctrl.py -f robot.create_all