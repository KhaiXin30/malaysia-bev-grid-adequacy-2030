"""Download raw open data from data.gov.my (JPJ registrations) into data/raw/.

    python src/fetch_data.py            # aggregate CSV + car transaction parquet files 2000-current
    python src/fetch_data.py --force    # re-download even if files exist

Policy and MAA PDFs used as sources are archived in data/raw/policy_docs and data/raw/maa_docs
(URLs in src/config.py SOURCES); they are not re-downloaded here.
"""
import argparse
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

AGG_URL = "https://storage.data.gov.my/transportation/registrations_type_fuel.csv"
TX_URL = "https://storage.data.gov.my/transportation/cars_{year}.parquet"


def _get(url: str, dest: Path, force: bool):
    if dest.exists() and not force:
        print(f"exists  {dest.relative_to(C.ROOT)}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "research-data-client"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(f"fetched {dest.relative_to(C.ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--first-year", type=int, default=2000)
    a = ap.parse_args()
    _get(AGG_URL, C.AGG_CSV, a.force)
    for y in range(a.first_year, date.today().year + 1):
        try:
            _get(TX_URL.format(year=y), C.TX_DIR / f"cars_{y}.parquet", a.force)
        except Exception as e:  # noqa: BLE001
            print(f"failed  cars_{y}.parquet: {e}")


if __name__ == "__main__":
    main()
