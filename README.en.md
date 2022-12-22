#  openeuler-obs

# Description

Open build service (OBS) system for openEuler community.

# Software Architecture

![](https://gitee.com/openeuler/G11N/raw/master/learning-materials/open-source-basics/images/1025_1.jpg)

# Function Description

| No.  |                       Function                        |                         Description                          |       Module       |
| :--: | :---------------------------------------------------: | :----------------------------------------------------------: | :----------------: |
|  1   |              Creates the OBS repository               | Creates an OBS empty repository or a spare repository of an existing repository based on the meta file in the [obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta) directory. |  project_manager   |
|  2   | Modifies the Meta configuration of the OBS repository | Modifies the configuration of the OBS repository based on the meta file in the [obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta) directory. |  project_manager   |
|  3   |              Deletes the OBS repository               | Deletes the corresponding OBS repository if the meta file in the [obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta) directory is deleted. |  project_manager   |
|  4   |  Creates the software packages of the OBS repository  | Creates the software packages and the _service file in the corresponding OBS repository based on the commit records of [obs_meta](https://gitee.com/src-openeuler/obs_meta). |  package_manager   |
|  5   |  Deletes the software packages of the OBS repository  | Deletes the software packages of the corresponding OBS repository based on the commit records of [obs_meta](https://gitee.com/src-openeuler/obs_meta). |  package_manager   |
|  6   | Modifies the software packages of the OBS repository  | Modifies the _service file of the software packages in the corresponding OBS repository based on the commit records of [obs_meta](https://gitee.com/src-openeuler/obs_meta). |  package_manager   |
|  7   |             Checks the software packages              | Checks the software packages, supplements the missing packages and deletes the package that do not exist based on the src-openeuler.yam file in the [community/repository](https://gitee.com/openeuler/community/tree/master/repository)/ directory and [obs_meta](https://gitee.com/src-openeuler/obs_meta). |  package_manager   |
|  8   |             Checks the software packages              | Checks the software packages, supplements the missing packages and deletes the package that do not exist based on the OBS repository and [obs_meta](https://gitee.com/src-openeuler/obs_meta). |  package_manager   |
|  9   |           Updates the software package code           | Synchronized the code in the software package repository to the OBS repository and sets the synchronization switch. (If the switch is on, the code synchronizes normally; if it is off, the code needs to be synchronized manually.) |    gitee_to_obs    |
|  10  |                    Checks obs_meta                    | Checks the new PR in the [obs_meta](https://gitee.com/src-openeuler/obs_meta) repository. | check_meta_service |
|  11  |     Archives the binary of the software packages      | Archives the binary in the [obs_meta](https://gitee.com/src-openeuler/obs_meta) repository to the binary depency repository. |  update_obs_repos  |

# Instructions

## 1. Run the following commands to pack the software packages.

（1）git clone https://gitee.com/openeuler/openeuler-obs
（2）pip3 install numpy pexpect pyinstaller PyYAML threadpool
（3）cd openeuler-obs
（4）pyinstaller openeuler_obs.py -p common/common.py -p common/log_obs.py -p common/parser_config.py -p core/check_meta_service.py -p core/gitee_to_obs.py -p core/package_manager.py -p core/project_manager.py -p core/runner.py -p core/save.py -p core/update_obs_repos.py --clean
（5）cd dist/openeuler_obs && cp ../../config ./ -rf

## 2. Usage

| Parameter           | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| obs_meta_path       | Directory path of the obs_meta repository                   |
| OBS_SOURCE_IP       | Server IP address for storing source code                   |
| OBS_SOURCE_PWD      | Server password for storing source code                     |
| OBS_BACKEND_IP      | IP address of the OBS server                                |
| OBS_BACKEND_PWD     | Password of the OBS server                                  |
| GiteeCloneUserName  | Gitee account name                                          |
| GiteeClonePassword  | Gitee account password                                      |
| obs_project_name    | OBS repository name                                         |
| repo_name           | Binary repository name                                      |
| arch_name           | Architecture name                                           |
| giteePullRequestlid | PR ID that has not been merged into the obs_meta repository |
| giteeTargetRepoName | Software package repository name                            |
| giteeTargetBranch   | Gitee branch name                                           |

●  Modifies the OBS repository based on the commit records of the obs_meta repository.
  Command:./openeuler_obs -r obs_meta -o <obs_meta_path> -ip <OBS_SOURCE_IP> -suser root -spwd <OBS_SOURCE_PWD> -guser -gpwd

●  Modifies the software packages in the OBS repository based on the commit records of the obs_meta repository.
  Command: ./openeuler_obs -r obs_meta -o <obs_meta_path> -ip <OBS_SOURCE_IP> -suser root -spwd <OBS_SOURCE_PWD> -guser -gpwd

●  Checks whether the software packages in the obs_meta and OBS repositories are consistent.
  Command: ./openeuler_obs -r obs_meta -o <obs_meta_path> -guser -gpwd --check_meta

●  Checks whether the software packages in the obs_meta and src-openeuler.yaml are consistent.
  Command: ./openeuler_obs -r obs_meta -o <obs_meta_path> -guser -gpwd --check_yaml

●  Updates the software package code.
  Command: ./openeuler_obs -r -o <obs_meta_path> -b -ip <OBS_SOURCE_IP> -suser root -spwd <OBS_SOURCE_PWD> -guser -gpwd

●  Checks obs_meta
  Command: ./openeuler_obs -cps -prid

●  Backs up and updates the binary of the software package in the binary repository.
  Command 1: ./openeuler_obs -up -p <obs_project_name> -repo <repo_name> -arch <arch_name> -rsip <OBS_BACKEND_IP> -rsu root -rsup <OBS_BACKEND_PWD> -guser -gpwd (Archives the binary of the all specified software packages in the OBS repository.)
  Command 2: ./openeuler_obs -up -p <obs_project_name> -repo <repo_name> -arch <arch_name> -rsip <OBS_BACKEND_IP> -rsu root -rsup <OBS_BACKEND_PWD> -guser -gpwd --pkglist  (Archives the binary of a single or multiple specified software packages in the OBS repository.)

# Contribution

1. Fork the repository
2.  Create Feat_xxx branch.
3.  Commit your code.
4. Create a new Pull Request.

# Gitee Feature

1. Readme\_XXX.md supports different languages. The file name examples are as follows: Readme\_en.md and Readme\_zh.md.
2. Get information or seek help from the Gitee official blogs by visiting https://blog.gitee.com.
3. Explore open source projects by visiting https://gitee.com/explore.
4. Get information about the most valuable open source project GVP by visiting https://gitee.com/gvp.
5. Obtain Gitee user guide by visiting https://gitee.com/help.
6. Get to know the most popular members by visiting https://gitee.com/gitee-stars.
