#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 12:38:21 2019

@author: fei.xu
"""
import argparse
import os

schedOptions="-V -cwd -b y -S /bin/bash -j y"

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def usage():
    argp = argparse.ArgumentParser(description='Write sjm jobs', formatter_class=argparse.RawTextHelpFormatter)
    argp.add_argument('-f', dest='sjmFile', help='sjm File', metavar='')
    argp.add_argument('-j', dest='jobName', help='job Name', metavar='')
    argp.add_argument('-p', dest='pe', help='pe', metavar='')
    argp.add_argument('-s', dest='slots', help='slots', metavar='')
    argp.add_argument('-c', dest='cmd', help='cmd', metavar='')
    argp.add_argument('-n', dest='newFile', type=str2bool, default=False, help='=True or False to indicate whether to keep old file', metavar='')
    argp.add_argument('-l', dest='local', type=str2bool, help='=True or False to indicate whether to execute locally', metavar='')
    args = argp.parse_args()

    if args.sjmFile and args.jobName and args.pe and args.slots and args.cmd:
        sjm_job_writer(sjmFile=args.sjmFile, jobName=args.jobName, pe=args.pe, slots=args.slots, cmd=args.cmd, newFile=args.newFile, local=args.local)

def sjm_job_writer(sjmFile, jobName, pe, slots, cmd, newFile, local):
    if newFile == True:
        os.system('rm -f '+sjmFile)
    print(newFile, local)
    with open(sjmFile, "a") as sjm_job_writer:
        if local == True:
            sjm_job_writer.writelines(
                'job_begin'
                    +'\n\tname '+jobName
                    +'\n\thost localhost'
                    +'\n\tcmd_begin'
                        +'\n\t\t'+cmd
                    +'\n\tcmd_end'
                +'\njob_end\n')
        else:
            sjm_job_writer.writelines(
                'job_begin'
                    +'\n\tname '+jobName
                    +'\n\tslots '+slots
                    +'\n\tparallel_env '+pe
                    +'\n\tsched_options '+schedOptions
                    +'\n\tcmd_begin'
                        +'\n\t\t'+cmd
                    +'\n\tcmd_end'
                +'\njob_end\n')

if __name__ == "__main__":

    usage()
