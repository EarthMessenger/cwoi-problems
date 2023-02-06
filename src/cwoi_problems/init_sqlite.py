'''
Init a sqlite database which cwoi_problems's crawler and server use

Warning: the database structure may update in further update
'''

import argparse
import os
import pathlib
import sqlite3
import sys


def create_database(db_dir):
    '''
    create a new sqlite database for cwoi-problems
    '''
    conn = sqlite3.connect(db_dir)
    cur = conn.cursor()
    cur.executescript('''
    DROP TABLE IF EXISTS submissions;
    CREATE TABLE submissions (
        id          TEXT NOT NULL PRIMARY KEY UNIQUE,
        problem_id  TEXT NOT NULL,
        contest_id  TEXT NOT NULL,
        user_id     TEXT NOT NULL,
        time        DATETIME NOT NULL,
        status      TEXT NOT NULL
    );
    DROP TABLE IF EXISTS contests;
    CREATE TABLE contests (
        id              TEXT NOT NULL PRIMARY KEY UNIQUE,
        begin_time      DATETIME NOT NULL,
        end_time        DATETIME NOT NULL,
        title           TEXT NOT NULL,
        display_id      TEXT NOT NULL UNIQUE,
        group_a         BOOL NOT NULL DEFAULT 0,
        group_b         BOOL NOT NULL DEFAULT 0,
        group_c         BOOL NOT NULL DEFAULT 0,
        group_d         BOOL NOT NULL DEFAULT 0,
        group_e         BOOL NOT NULL DEFAULT 0,
        group_unknown   BOOL NOT NULL DEFAULT 0
    );
    DROP TABLE IF EXISTS users;
    CREATE TABLE users (
        id          TEXT NOT NULL PRIMARY KEY UNIQUE,
        name        TEXT NOT NULL
    );
    DROP TABLE IF EXISTS problems;
    CREATE TABLE problems (
        id      TEXT NOT NULL PRIMARY KEY UNIQUE,
        title   TEXT NOT NULL
    );
    DROP TABLE IF EXISTS contest_to_problem;
    CREATE TABLE contest_to_problem (
        contest_id          TEXT NOT NULL,
        problem_display_id  TEXT NOT NULL,
        problem_id          TEXT NOT NULL
    );
    ''')
    conn.commit()
    conn.close()


def main():
    '''
    main function of this script.
    providing a friendly output.
    '''
    parser = argparse.ArgumentParser(
        description='Create a new sqlite database for cwoi-problems')
    parser.add_argument('database_dir', type=pathlib.Path,
                        help='where to create a new sqlite database')
    args = parser.parse_args()
    db_dir = vars(args)['database_dir']
    if os.path.exists(db_dir):
        print(
            f'{db_dir} already exits, remove it if you really want to create a new one')
        sys.exit()
    create_database(db_dir)
    print(f'successfully created {db_dir}')


if __name__ == '__main__':
    main()
