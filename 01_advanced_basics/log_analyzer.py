#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import gzip
import datetime
import string
import json
import statistics
import sys
import getopt
import logging

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def get_config(config_file=''):
    result_config = config
    config_items = ("REPORT_SIZE",
                    "REPORT_DIR",
                    "LOG_DIR")
    parse_conf = {}
    if config_file:
        with open(config_file, 'r') as cf:
            for line in cf:
                if line.startswith(config_items):
                    sp_line = line.split(":")
                    parse_conf[sp_line[0]] = "".join(
                                    sp_line[1:]).strip('\n" ')
    result_config.update(parse_conf)
    return result_config

def get_log_files(directory):
    files_list = [f for f in os.listdir(
                  directory) if os.path.isfile(
                  directory+'/'+f) and f.startswith('nginx-access-ui')]
    files_with_date = []
    pattern = re.compile(r"nginx-access-ui\.log-(\d*)(\.gz)?")
    for f in files_list:
        files_with_date.append(( directory+'/'+f , 
                        datetime.datetime.strptime(
                        re.search(pattern, f).group(1), '%Y%m%d' )))
    files_with_date.sort(key=lambda r: r[1])
    if not files_with_date:
        logging.info('Files not found')
    for f in files_with_date:
        yield f

def get_message_from_file(filename):
    if filename.endswith('.gz'):
        with gzip.open(filename, 'rb') as f:
            for message in f:
                yield str(message)
    else:    
        with open(filename, 'r') as f:
            for message in f:
                yield message


def parse_log_massage(message):
    url, request_time, error = ('', 0, False)
    try:
        list_of_m = message.split(' ')
        url = list_of_m[7]
        request_time = round(float(list_of_m[-1].rstrip("\\n\'")),3)
    except Exception:
        error = True
    return url, request_time, error

def perc(count_all, count):
    return round(count * 100 / count_all, 3)

def check_error_count(all_message, error_count, threshold):
    if perc(all_message, error_count ) > threshold:
        logging.info('Errors threshold exceeded')
        return False
    return True

def get_report_name(date, report_dir):
    return report_dir+'/report_{}.html'.format(date.strftime(
                                    "%Y.%m.%d"))
        

def main(argv):
    opts, _ = getopt.getopt(argv,"",["config="])
    if opts and opts[0][0] == '--config':
        conf = get_config(opts[0][1])
    else: 
        conf = get_config()
    if conf['LOG_DIR']:
        logfile=conf['LOG_DIR']+"/log_analyzer.log"
    else:
        logfile=None
    logging.basicConfig(filename=logfile,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S',
                        level=logging.INFO)

    result_dict = {}
    NUM_REQUESTS = 0
    SUM_TIME = 0
    try:
        for i in get_log_files("."):
            error_count = 0
            if os.path.isfile(get_report_name(
                i[1],
                conf["REPORT_DIR"]
            )): 
                logging.info(f"work with file {i[0]} already done")
                continue
            for x in get_message_from_file(i[0]):
                url, r_time, error = parse_log_massage(x)
                current = result_dict.get(url, {
                    "count" : 0,
                    "time_sum": 0,
                    "time_avg": 0,
                    "time_max": 0,
                    "time_values" : [] 
                })
                current["count"]+=1
                current["time_sum"]+=r_time
                current["time_avg"]=current["time_sum"]/current["count"]
                current["time_max"]=r_time if r_time > current["time_max"] \
                                    else current["time_max"]
                current["time_values"].append(r_time)
                result_dict.setdefault(url,current)
                result_dict[url]=current
                NUM_REQUESTS +=1
                SUM_TIME +=r_time
                if error:
                    error_count+=1
            if not check_error_count(NUM_REQUESTS,
                                error_count,
                                40):
                sys.exit(1)                
            RESULT_LIST = []
            for k, v in result_dict.items():
                item = {
                    "count": v["count"],
                    "time_sum": round(v["time_sum"],3),
                    "time_avg": round(v["time_avg"],3),
                    "time_max": v["time_max"]
                } 
                item["url"] = k
                item["time_med"] = round(statistics.median(v["time_values"]),3)
                item["count_perc"] = perc(NUM_REQUESTS,v["count"])
                item["time_perc"] = perc(SUM_TIME, v["time_sum"])
                RESULT_LIST.append(item)
            del result_dict
            RESULT_LIST=sorted(RESULT_LIST, 
                                key=lambda r: r["time_sum"], reverse=True)
            RESULT_LIST = RESULT_LIST[:int(conf["REPORT_SIZE"]):]
            with open('report.html', 'r') as f:
                s = string.Template(f.read())
                result_string = s.safe_substitute(
                                table_json=json.dumps(RESULT_LIST))
                with open(get_report_name(i[1],conf["REPORT_DIR"]),
                                          'w') as save_f:
                    save_f.write(result_string)
    except Exception as e:
        logging.exception(f"Exception occurred {e}")    
    

if __name__ == "__main__":
        main(sys.argv[1:])