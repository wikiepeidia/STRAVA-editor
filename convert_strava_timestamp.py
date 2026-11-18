from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"
GPX_NAMESPACES = {
    "": GPX_NAMESPACE,
    "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
    "gpxx": "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
}


for prefix, uri in GPX_NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Shift Strava GPX timestamps so the activity starts today at 18:00 GMT+7 "
            "while preserving the original elapsed time between points."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="Afternoon_Run.gpx",
        help="Source GPX file. Defaults to Afternoon_Run.gpx in the current folder.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output GPX path. Defaults to <input>_today_18_gmt7.gpx.",
    )
    parser.add_argument(
        "--date",
        help="Target local date in YYYY-MM-DD. Defaults to today in GMT+7.",
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=18,
        help="Target local start hour. Defaults to 18.",
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="Target local start minute. Defaults to 0.",
    )
    parser.add_argument(
        "--timezone-offset",
        type=int,
        default=7,
        help="Target timezone offset from UTC in hours. Defaults to 7.",
    )
    return parser.parse_args()


def parse_timestamp(value: str) -> datetime:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"
    return datetime.fromisoformat(cleaned)


def format_timestamp(value: datetime) -> str:
    utc_value = value.astimezone(timezone.utc).replace(microsecond=0)
    return utc_value.isoformat().replace("+00:00", "Z")


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_today_18_gmt7{input_path.suffix}")


def resolve_target_start(args: argparse.Namespace) -> datetime:
    target_timezone = timezone(timedelta(hours=args.timezone_offset))
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = datetime.now(target_timezone).date()

    return datetime.combine(
        target_date,
        time(hour=args.hour, minute=args.minute),
        tzinfo=target_timezone,
    )


def collect_time_elements(root: ET.Element) -> list[ET.Element]:
    return root.findall(f".//{{{GPX_NAMESPACE}}}time")


def shift_gpx_timestamps(input_path: Path, output_path: Path, target_start: datetime) -> tuple[datetime, datetime]:
    tree = ET.parse(input_path)
    root = tree.getroot()
    time_elements = collect_time_elements(root)

    if not time_elements:
        raise ValueError(f"No <time> elements found in {input_path}")

    original_start = parse_timestamp(time_elements[0].text or "")
    offset = target_start.astimezone(timezone.utc) - original_start

    for time_element in time_elements:
        original_time = parse_timestamp(time_element.text or "")
        time_element.text = format_timestamp(original_time + offset)

    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    return original_start, original_start + offset


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else default_output_path(input_path)
    target_start = resolve_target_start(args)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    original_start, new_start = shift_gpx_timestamps(input_path, output_path, target_start)

    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Original start (UTC): {format_timestamp(original_start)}")
    print(f"New start (UTC):      {format_timestamp(new_start)}")
    print(f"New start (GMT+7):    {target_start.replace(microsecond=0).isoformat()}")


if __name__ == "__main__":
    main()