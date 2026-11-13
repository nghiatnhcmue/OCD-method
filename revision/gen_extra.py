"""Sinh tập chọn tham số (tune) và tập khóa (locked) bằng đúng hai bộ sinh của Kiểm tra 1 và 2, với khối seed mới."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

GEN = S.REPO / "research" / "phat_trien_v2" / "kiem_tra_luan_van.py"
OUT = S.ROOT / "data_extra"
KT1_CELLS = ((0, 2), (200, 4), (400, 6))
BASES = {"tune": (993_000_000, 993_500_000), "locked": (994_000_000, 994_500_000)}


def module():
    spec = importlib.util.spec_from_file_location("kiem_tra_luan_van", GEN)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def main(which):
    m = module()
    b1, b2 = BASES[which]
    m.sinh_lfr_bo_chinh("%s_kt1" % which, OUT / ("%s_kt1" % which), 1000, KT1_CELLS, (1,), b1)
    m.sinh_lfr_goc("%s_kt2" % which, OUT / ("%s_kt2" % which), 1000, m.KT2_MU, m.KT2_O, (1,), b2)


if __name__ == "__main__":
    main(sys.argv[1])
