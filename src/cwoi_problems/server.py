'''
Provide a web-based interface.
'''

import sqlite3
import argparse
import pathlib

import flask
import flask_caching

app = flask.Flask(__name__)
app.config.from_mapping({
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
})
cache = flask_caching.Cache(app)


def get_db_connection():
    '''
    get db connection from flask global or return a new one
    '''
    conn = getattr(flask.g, 'database', None)
    if conn is None:
        conn = flask.g.database = sqlite3.connect(DATABASE)
    return conn


@app.teardown_appcontext
def close_connection(exception):
    '''
    close db connection in the flask global
    '''
    conn = getattr(flask.g, 'database', None)
    if conn is not None:
        conn.close()


@app.route('/')
@cache.cached(timeout=86400)
def index():
    '''
    index page shows all the contests and problems
    '''
    cur = get_db_connection().cursor()
    contests = {}
    for i in cur.execute(
            'SELECT id, title, display_id FROM contests ORDER BY begin_time DESC').fetchall():
        contests[i[0]] = {'title': i[1], 'display_id': i[2], 'problems': {}}

    problems = {}
    for i in cur.execute('SELECT id, title FROM problems').fetchall():
        problems[i[0]] = i[1]
    for i in cur.execute(
            'SELECT contest_id, problem_display_id, problem_id FROM contest_to_problem ORDER BY problem_display_id ASC').fetchall():
        contests[i[0]]['problems'][i[1]] = problems[i[2]]
    resp = flask.make_response(flask.render_template(
        'index.html', contests=contests, cwoi=CWOI_PREFIX))
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run a server to provide web-based ui')
    parser.add_argument('cwoi', type=str,
                        help='for example, https://local.cwoi.com.cn:8443, without a slash ending')
    parser.add_argument('database', type=pathlib.Path,
                        help='where your database is created')
    parser.add_argument('--port', type=int, default=5000,
                        help='where the server is opened')
    args = parser.parse_args()
    DATABASE = args.database
    CWOI_PREFIX = args.cwoi
    app.run(port=args.port)
