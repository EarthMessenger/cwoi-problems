"""
crawler for cwoi
"""

import argparse
import datetime
import time
import logging
import base64
import json

import requests

logger = logging.getLogger(__name__)


def base64_url_decode(s):
    """
    append missing = at the end of the str, then call urlsafe base64, witch is
    used in jwt.
    """
    r = len(s) % 4
    if r > 0:
        s += "=" * (4 - r)
    return base64.urlsafe_b64decode(s)


def get_jwt_exp(token):
    payload = token.split(".")[1]
    decoded = base64_url_decode(payload)
    return json.loads(decoded)["exp"]


class User:
    """
    class for storage a user's name, password and jwt token
    """

    def __init__(self, name: str, password: str, cwoi: str):
        self.cwoi = cwoi
        self.name = name
        self.password = password
        self.token = ""
        self.exp_timestamp = 0.0
        self.login()

    def update_exp(self):
        self.exp_timestamp = get_jwt_exp(self.token)

    def login(self):
        req = requests.post(
            f"{self.cwoi}/api/user/login",
            json={"login": self.name, "password": self.password, "remember": True},
        )
        req.raise_for_status()
        self.token = req.json()["token"]
        self.update_exp()
        logger.warning(f"login as {self.name}.")

    def renew(self):
        req = requests.post(
            f"{self.cwoi}/api/user/renewToken",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        req.raise_for_status()
        self.token = req.json()["token"]
        self.update_exp()
        logger.info(f"renew {self.name}'s token, exp: {self.exp_timestamp}")

    def get_token(self):
        cur_time = time.time()
        if self.exp_timestamp < cur_time:
            self.login()
        elif self.exp_timestamp < cur_time + 60:
            self.renew()
        return self.token

    def get_header(self):
        return {"Authorization": f"Bearer {self.get_token()}"}


class CwoiClient:
    """
    cwoi client for crawling

    user: The user that the crawler will impersonate
    sleep: The interval between two requests
    cwoi: CWOI host, for example, https://local.cwoi.com.cn:8443, without a slash ending
    """

    def __init__(self, user: User, cwoi: str, sleep: float):
        self.user = user
        self.cwoi = cwoi
        self.sleep = sleep

    def crawl_one_contest(self, _id: str, display_id: str):
        """
        crawl one contest and all the problem in it

        This fucking OJ uses two fucking different id to identify contest, fuck.
        """

        res = requests.get(
            f"{self.cwoi}/api/contest/id/{_id}/inContest",
            headers=self.user.get_header(),
        )
        if res.text == "false":
            res = requests.post(
                f"{self.cwoi}/api/contest/{_id}/join",
                headers=self.user.get_header(),
                json={"vp": True},
            )
        res = requests.get(
            f"{self.cwoi}/api/contest/displayid/{display_id}",
            headers=self.user.get_header(),
        )
        res.raise_for_status()
        logger.info(f"crawled contest {display_id}.")
        data = res.json()
        return {
            "_id": data["_id"],
            "contestDisplayId": data["contestDisplayId"],
            "contestTitle": data["contestTitle"],
            "problems": data["problems"],
            "startedAt": datetime.datetime.fromisoformat(data["startedAt"]).timestamp(),
            "endedAt": datetime.datetime.fromisoformat(data["endedAt"]).timestamp(),
            "groups": data["groups"],
        }

    def crawl_contests(self):
        """
        crawl contests after the lastest contest in the database
        """
        tot_pages = 1
        current_page = 1
        contests = []
        while current_page <= tot_pages:
            url = f"{self.cwoi}/api/contests?page={current_page}&pageSize=100"
            res = requests.get(
                url,
                headers=self.user.get_header(),
            )
            res.raise_for_status()
            logger.info(f"crawled url {url}")
            data = res.json()
            tot_pages = data["totalPages"]
            for i in data["rows"]:
                contests.append(self.crawl_one_contest(i["_id"], i["contestDisplayId"]))
                time.sleep(self.sleep)
            current_page += 1
            time.sleep(self.sleep)
        return contests


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Crawler for cwoi")
    parser.add_argument("name", type=str)
    parser.add_argument("password", type=str)
    parser.add_argument(
        "cwoi",
        type=str,
        help="For example, https://local.cwoi.com.cn:8443, without a slash ending",
    )
    parser.add_argument(
        "--sleep", type=float, default=1.0, help="the interval between two web requests"
    )
    args = parser.parse_args()

    client = CwoiClient(
        User(args.name, args.password, args.cwoi), args.cwoi, args.sleep
    )

    res = client.crawl_contests()
    print(json.dumps(res))


if __name__ == "__main__":
    main()
