#!/bin/bash
cd /home/nghia/wghac/wghac_wom_improve/Thuc_Nghiem
for ds in test1 test2 test3; do
  python3 -u -c "import sys; sys.path.insert(0, '.'); from common.runner import run_dataset; run_dataset('$ds', '$1', ['--workers', '$2'])"
done
echo ALL_DONE
