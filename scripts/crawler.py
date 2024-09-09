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


def base64_url_decode(s: str):
    """
    append missing = at the end of the str, then call urlsafe base64, witch is
    used in jwt.
    """
    r = len(s) % 4
    if r > 0:
        s += "=" * (4 - r)
    return base64.urlsafe_b64decode(s)


def get_jwt_exp(token: str):
    payload = token.split(".")[1]
    decoded = base64_url_decode(payload)
    return json.loads(decoded)["exp"]


def remove_bracket(name: str):
    """
    remove beginning 【】

    example:
    >>> remove_bracket("【a】b")
    'b'
    >>> remove_bracket("a【a】b")
    'a【a】b'
    >>> remove_bracket("a【ab")
    'a【ab'
    >>> remove_bracket("【ab")
    '【ab'
    >>> remove_bracket("[a]b")
    '[a]b'
    """
    if name[0] == "【":
        right = name.find("】")
        if right != -1:
            name = name[right + 1 :]
    return name.strip()


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

        data = res.json()
        return {
            "_id": data["_id"],
            "contestDisplayId": data["contestDisplayId"],
            "contestTitle": data["contestTitle"],
            "problems": data["problems"],
        }

    def check_contest_permission(self, _id: str):
        """
        if user is root, don't use this.
        check if user is in the contest, if not then vp it.
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

    def crawl_contest_problems(self, display_id: str):
        """
        crawl contest problems title and judge config id.
        """

        res = requests.get(
            f"{self.cwoi}/api/contest/displayid/{display_id}",
            headers=self.user.get_header(),
        )
        res.raise_for_status()
        raw_problems = res.json()["problems"]
        problems = []
        for p in raw_problems:
            res = requests.get(
                f"{self.cwoi}/api/contest/{display_id}/problem/{p['displayId']}",
                headers=self.user.get_header(),
            )
            res.raise_for_status()
            problem_info = res.json()
            if problem_info["judgeConfig"]:
                problem_id = problem_info["judgeConfig"]["problemId"]
            else:
                problem_id = "ghost"
            problems.append(
                {
                    "displayId": p["displayId"],
                    "problemTitle": remove_bracket(p["problemTitle"]),
                    "problemId": problem_id,
                }
            )
        return problems

    def crawl_contests(self):
        """
        crawl all contests. assume that the contest list would not change while crawling.
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
                contest = {
                    "_id": i["_id"],
                    "contestDisplayId": i["contestDisplayId"],
                    "contestTitle": i["contestTitle"],
                    "startedAt": datetime.datetime.fromisoformat(
                        i["startedAt"]
                    ).timestamp(),
                    "endedAt": datetime.datetime.fromisoformat(
                        i["endedAt"]
                    ).timestamp(),
                    "groups": i["groups"],
                    "problems": [],
                }

                if contest["endedAt"] <= datetime.datetime.now().timestamp():
                    if self.user.name != "root":
                        self.check_contest_permission(contest["_id"])
                    contest["problems"] = self.crawl_contest_problems(
                        contest["contestDisplayId"]
                    )

                contests.append(contest)

                logger.info(f"crawled contest {contest['contestDisplayId']}.")

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

    contests = client.crawl_contests()
    print(json.dumps(contests))


if __name__ == "__main__":
    main()
