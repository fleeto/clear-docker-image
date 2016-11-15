#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
import subprocess
import json
import time
from datetime import datetime


def main(condition, hash_only, action):

    # db in memory
    con = sqlite3.connect(':memory:')
    cur = con.cursor()
    cur.execute("CREATE TABLE images (id INTEGER PRIMARY KEY,image_id TEXT, image_name TEXT, image_tag TEXT, created INTEGER, image_size INTEGER);")

    fp = open("conf.json")
    conf = json.load(fp)
    cmd_list = conf["docker"]["list_command"]
    image_list_str = subprocess.check_output(cmd_list)

    # split the result into records
    lines = image_list_str.split("\n")
    for line in lines:
        line = line.strip('\'')
        segments = line.split(",")
        if len(segments) != 5:
            continue
        image_id = segments[0]
        image_name = segments[1]
        image_tag = segments[2]
        create = datetime.strptime(segments[3][:19], "%Y-%m-%d %H:%M:%S").timetuple()
        create = int(time.mktime(create))
        size = segments[4]
        sql = 'insert into images (image_id, image_name, image_tag, created, image_size) values \
        ("{}", "{}", "{}", {}, "{}")'
        sql = sql.format(image_id, image_name, image_tag, create, size)
        cur.execute(sql)

    condition = conf["sql"][condition]
    hash_list = []
    output_list = []
    if hash_only == 1:
        sql = "select image_id from images where " + condition
        for row in cur.execute(sql):
            output_list += [row[0]]
            hash_list = hash_list + [row[0]]
    else:
        sql = "select image_id, image_name, image_tag, created, image_size from images where " + condition
        for row in cur.execute(sql):
            hash_list = hash_list + [row[0]]
            output_list += ["{}\t{}\t{}\t{}\t{}".format(
                row[0], row[1], row[2], row[3], row[4])]

    if action != "none":
        for hash_value in hash_list:
            cmd = conf["docker"]["action_command"] + [action] + [hash_value]
            try:
                subprocess.check_call(cmd)
            except:
                continue

    else:
        for line in output_list:
            print line

if __name__ == "__main__":
    if (len(sys.argv) == 4):
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    else:
        print "Usage %s sql_id if_hash_only action " % sys.argv[0]
