"""
read a json from stdin, then build htmls using jinja2 to dist/
"""

import logging
import argparse
import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

logger = logging.getLogger(__name__)


def build_html(data: Path, dist: Path, cwoi: str):
    env = Environment(loader=PackageLoader(__package__), autoescape=select_autoescape())
    template = env.get_template("index.html.jinja")
    with data.open("r") as inf:
        contests = json.load(inf)
    with (dist / "index.html").open("w") as ouf:
        ouf.write(template.render(contests=contests, cwoi=cwoi))


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Build html from crawled contests.json"
    )
    parser.add_argument("data", type=Path, help="where contests.json is located")
    parser.add_argument("dist", type=Path, help="where the htmls should be written")
    parser.add_argument(
        "cwoi",
        type=str,
        help="For example, https://local.cwoi.com.cn:8443, without a slash ending",
    )
    args = parser.parse_args()

    build_html(args.data, args.dist, args.cwoi)


if __name__ == "__main__":
    main()
