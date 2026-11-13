#!/bin/bash
cd /home/nghia/wghac/wghac_wom_improve/Thuc_Nghiem
python3 -u revision/trees.py --sets lock1 lock2 --workers 9
python3 -u revision/phase2.py --sets lock1 lock2 --configs cp_node_0.05 --workers 10
echo LOCKED_DONE
