#!/bin/bash
cd /home/nghia/wghac/wghac_wom_improve/Thuc_Nghiem
for ds in lock1 lock2; do
  python3 -u -c "import sys; sys.path.insert(0, '.'); from common.runner import run_dataset; run_dataset('$ds', 'oslom', ['--workers', '1'])"
done
echo OSLOM_DONE
