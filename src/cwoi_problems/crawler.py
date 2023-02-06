'''
crawler for cwoi
'''

import argparse
import datetime
import pathlib
import sqlite3
import time
from dataclasses import dataclass

import requests
import dateutil.parser


@dataclass
class User:
    '''
    class for storage a user's name and password
    '''
    name: str
    password: str


class CwoiClient:
    '''
    cwoi client for crawling

    user: The user that the crawler will impersonate
    sleep: The interval between two requests
    cwoi_prefix: For example, https://local.cwoi.com.cn:8443, without a slash ending
    database: The connection of sqlite database
    '''

    def __init__(self, user: User, cwoi_prefix: str, sleep: float, database: sqlite3.Connection):
        self.user = user
        self.cwoi_prefix = cwoi_prefix
        self.sleep = sleep
        self.database = database
        self.token = ''
        self.latest_renew = datetime.datetime.min
        self.login()

    def login(self):
        '''
        login with the provided username and password
        '''
        login_request = requests.post(
            f'{self.cwoi_prefix}/api/user/login',
            json={'login': self.user.name,
                  'password': self.user.password, 'remember': True},
            timeout=5)
        login_request.raise_for_status()
        print(f'login as {self.user.name} successfully')
        self.token = login_request.json()['token']
        self.latest_renew = datetime.datetime.now()

    def renew_token(self):
        '''
        renew the token if now - self.latest_renew = 10min
        '''
        if datetime.datetime.now() - self.latest_renew > datetime.timedelta(minutes=10):
            renew_requet = requests.post(
                f'{self.cwoi_prefix}/api/user/renewToken',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=5)
            renew_requet.raise_for_status()
            print(f'renew {self.user.name}\'s token successfully')
            self.token = renew_requet.json()['token']
            self.latest_renew = datetime.datetime.now()

    def get_token(self):
        '''
        renew the token, then return the token.
        '''
        self.renew_token()
        return f'Bearer {self.token}'

    def crawl_one_contest(self, normal_id: str, display_id: str, cur: sqlite3.Cursor):
        '''
        crawl one contest and all the problem in it

        This fucking OJ uses two fucking different id to identify contest, fuck.
        '''

        # if the contest have already crawled, skip it
        if not cur.execute('SELECT id FROM contests WHERE id = ?', (normal_id,)).fetchone() is None:
            return

        url = f'{self.cwoi_prefix}/api/contest/displayid/{display_id}'
        res = requests.get(url,
                           headers={'Authorization': self.get_token()},
                           timeout=5)
        res.raise_for_status()
        print(f'crawled contest {url}')
        data = res.json()
        # refers to init_sqlite.py to see how the database defined
        contest_info = [
            data['_id'],
            int(dateutil.parser.parse(data['startedAt']).timestamp()),
            int(dateutil.parser.parse(data['endedAt']).timestamp()),
            data['contestTitle'], data['contestDisplayId'], 0, 0, 0, 0, 0, 0]
        for group in data['groups']:
            match group:
                case 'A组':
                    contest_info[5] = 1
                case 'B组':
                    contest_info[6] = 1
                case 'C组':
                    contest_info[7] = 1
                case 'D组':
                    contest_info[8] = 1
                case 'E组':
                    contest_info[9] = 1
                case _:
                    contest_info[10] = 1
        cur.execute(
            'INSERT OR IGNORE INTO contests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', contest_info)

        for prob in data['problems']:
            cur.execute('INSERT OR IGNORE INTO problems VALUES (?, ?)',
                        (prob['problemId'], prob['problemTitle']))
            cur.execute('INSERT INTO contest_to_problem VALUES (?, ?, ?)',
                        (normal_id, prob['displayId'], prob['problemId']))

    def crawl_contests_after(self):
        '''
        crawl contests after the lastest contest in the database
        '''
        cur = self.database.cursor()
        tot_page = 1
        current_page = 1
        while current_page <= tot_page:
            url = f'{self.cwoi_prefix}/api/contests?page={current_page}&pageSize=100'
            res = requests.get(url,
                               headers={'Authorization': self.get_token()},
                               timeout=5)
            res.raise_for_status()
            print(f'crawled url {url}')
            data = res.json()
            tot_page = data['totalPages']
            for ele in data['rows']:
                self.crawl_one_contest(
                    ele['_id'], ele['contestDisplayId'], cur)
                time.sleep(self.sleep)
            current_page += 1
            self.database.commit()
            time.sleep(self.sleep)


def main():
    '''
    main function of the script
    '''
    parser = argparse.ArgumentParser(description='Crawler for cwoi')
    parser.add_argument('username', type=str,
                        help='the user that the crawler will impersonate')
    parser.add_argument('password', type=str, help='the password of the user')
    parser.add_argument('cwoi', type=str,
                        help='For example, https://local.cwoi.com.cn:8443, without a slash ending')
    parser.add_argument('database', type=pathlib.Path,
                        help='where sqlite database is located')
    parser.add_argument('--sleep', type=float, default=1.0,
                        help='the interval between two web requests')
    args = parser.parse_args()
    with sqlite3.connect(args.database) as database:
        client = CwoiClient(User(args.username, args.password),
                            args.cwoi, args.sleep, database)
        client.crawl_contests_after()


if __name__ == '__main__':
    main()
