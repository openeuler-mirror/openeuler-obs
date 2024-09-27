import numpy as np
import pandas as pd
import xlwt
import os
import yaml
import datetime


par = argparse.ArgumentParser()
par.add_argument("-tbr", "--to_branch", default=None,
        help="which to branch you choose", required=True)
par.add_argument("-fbr", "--from_branch", default=None,
        help="which from branch you choose", required=True)
args = par.parse_args()


datestr = datetime.datetime.now().strftime('%Y-%m-%d') 
baseos_list = os.popen("cat baseos.list").read().split("\n")


def read_result(filename):
    result = {}
    #读取excel中所有数据
    file_path = os.path.join(os.getcwd(),filename)
    data = pd.read_excel(file_path)
    data.columns=["pkgname","project","gitee_status","build_status","install_status",'basey']
    for index,row in data.iterrows():
        pkg = row['pkgname']
        project = row['project']
        result[pkg] = project
    print (result)
    return result

def get_project_packages(all_dict,from_branch,to_branch):
    #读取excel中所有数据
    data = pd.read_excel('./{}.xlsx'.format(args.to_branch))
    data.columns=["pkgname",'project','status']
    i = 0
    j = 0
    for index,row in data.iterrows():
        pkg = row['pkgname']
        project = row['project']
        if project in ['openEuler:master:Epol']:
            pkg_info = {
                    "name": pkg,
                    "source_dir": from_branch,
                    "destination_dir": to_branch,
                    "date": datestr
            }
            j += 1
            all_dict['epol']['packages'].append(pkg_info)
        elif pkg in baseos_list:
            pkg_info = {
                    "name": pkg,
                    "source_dir": from_branch,
                    "destination_dir": to_branch,
                    "date": datestr
        }
            all_dict['baseos']['packages'].append(pkg_info)
            i += 1
        else:
            pkg_info = {
                    "name": pkg,
                    "source_dir": from_branch,
                    "destination_dir": to_branch,
                    "date": datestr
        }
            all_dict['everything-exclude-baseos']['packages'].append(pkg_info)
            i += 1
    print ("{} pkgs: {}".format(args.to_branch, i))
    print ("{} epol pkgs: {}".format(args.to_branch, j))
    return all_dict

def get_private_path_pkgname(private_sig_path):
    '''
    get private sig pkg name from sig path
    params
    private_sig_path : private sig path in community repo
    '''
    private_sig_pkgs = []
    for filepath,dirnames,filenames in os.walk(private_sig_path):
        for file in filenames:
            head,sep,tail = file.partition('.')
            private_sig_pkgs.append(head)
    return private_sig_pkgs

def check_private_sig_pkg(pkg_name):
    '''
    check add pkg include in private sig 
    params
    chang_file : modified file abs path
    '''
    pkg_names = 
    private_sig_path = os.path.join(os.getcwd(), "community", "sig", "sig-recycle","src-openeuler")
    private_sig_pkgs = get_private_path_pkgname(private_sig_path)
    failed_msg = []
    if pkg_name in private_sig_pkgs:
        pkg_names.append(pkg_name)
        print ("private_sig_pkgs:{}".format(pkg_name))
    return pkg_names


def step_write(all_dict):
    for key,value in all_dict.items():
        dir_path = os.path.join(os.getcwd(), '{}/{}'.format(args.to_branch,key))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        yaml_path = os.path.join(dir_path,"pckg-mgmt.yaml")
        write_yaml(value,yaml_path)

def write_yaml(dict_msg, file_path):
    with open(file_path, "w", encoding='utf-8') as f:
        yaml.dump(dict_msg, f, default_flow_style=False, sort_keys=False)

from_branch = args.to_branch
to_branch = args.from_branch
all_dict = {'baseos':{'packages':[]},'everything-exclude-baseos':{'packages':[]},'epol':{'packages':[]},'delete':{'packages':[]}}
all_dict = get_project_packages(all_dict, from_branch, to_branch)
step_write(all_dict)