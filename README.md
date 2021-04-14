# openeuler-obs

#### 介绍
Open build service system for openEuler community.

#### 软件架构
软件架构说明
![输入图片说明](https://images.gitee.com/uploads/images/2020/1201/225845_f7674b15_6525505.png "Snipaste_2020-12-01_22-44-19.png")
#### 功能列表
| 序号   | 功能  | 详细描述  | 模块名 |
|----|---|---|---|
|  1  | 创建obs仓库 | 根据[obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件创建obs空仓或obs已有仓库的备份仓库   | project_manager |
|  2  | 修改obs仓库的Meta配置 | 根据[obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件修改obs仓库的配置   | project_manager |
|  3  | 删除obs仓库 | [obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件被删除，则删除对应的obs仓库  | project_manager |
|  4  | 创建obs仓库软件包  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，在obs对应仓库中创建软件包及软件包下的_service文件  | package_manager |
|  5  | 删除obs仓库软件包  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，删除obs对应仓库中的软件包  | package_manager |
|  6  | 修改obs仓库软件包的_service  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，修改obs对应仓库中创建软件包的_service文件  | package_manager |
|  7  | 软件包检查 | 根据[community/repository](https://gitee.com/openeuler/community/tree/master/repository)/目录下的src-openeuler.yam文件及[obs_meta](https://gitee.com/src-openeuler/obs_meta)对obs仓库的软件包进行检视，补充缺少的软件包、删除码云上不存在的软件包  | package_manager |
|  8  | 软件包检查 | 根据obs仓库及[obs_meta](https://gitee.com/src-openeuler/obs_meta)对obs仓库的软件包进行检视，补充缺少的软件包、删除obs_meta中不存在的软件包 |  package_manager |
|  9  | 软件包代码更新 | 将码云软件包仓库的代码同步到obs仓库，设置同步开关(开关打开：正常同步;开关关闭：代码不同步，如需同步则后续人工同步) | gitee_to_obs |
|  10  | obs_meta合规检查 | 对[obs_meta](https://gitee.com/src-openeuler/obs_meta)仓库提交有关新增包PR的内容进行合规检查 | check_meta_service |
|  11  | 归档软件包二进制 | 将obs仓库软件包的二进制归档到二进制依赖仓库中 | update_obs_repos |

#### 使用说明

1.  **工具打包** 	    
（1）git clone https://gitee.com/openeuler/openeuler-obs	    
（2）pip3 install numpy pexpect pyinstaller PyYAML threadpool	    
（3）cd openeuler-obs	    
（4）pyinstaller openeuler_obs.py -p common/common.py -p common/log_obs.py -p common/parser_config.py -p core/check_meta_service.py -p core/gitee_to_obs.py -p core/package_manager.py -p core/project_manager.py -p core/runner.py -p core/save.py -p core/update_obs_repos.py --clean	    
（5）cd dist/openeuler_obs && cp ../../config ./ -rf	    
&emsp;完成以上操作后，即可使用。	    
2.  **使用** 	

|变量名称|含义|
|--------------------|-----------------|
| obs_meta_path      | obs_meta仓库的目录路径 |
| OBS_SOURCE_IP      | 存放源码服务器的IP地址     |
| OBS_SOURCE_PWD     | 存放源码服务器的密码       |
| OBS_BACKEND_IP     | obs服务器的IP地址     |
| OBS_BACKEND_PWD    | obs服务器的密码       |
| GiteeCloneUserName | 码云账号名称          |
| GiteeClonePassword | 码云账号密码          |
| obs_project_name   | obs仓库名称         |
| repo_name          | 二进制仓库名称         |
| arch_name          | 架构名称            |
| giteePullRequestlid | obs_meta仓库未合入的PR号 |
| giteeTargetRepoName | 软件包仓库名称           |
| giteeTargetBranch   | 码云分支名称            |

&emsp;&emsp;● 根据obs_meta仓库的提交记录对obs仓库进行增删改操作	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o <obs_meta_path> -ip <OBS_SOURCE_IP> -suser root -spwd <OBS_SOURCE_PWD> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword>        
&emsp;&emsp;● 根据obs_meta仓库的提交记录对obs仓库的软件包进行增删改操作	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o <obs_meta_path> -ip <OBS_SOURCE_IP> -suser root -spwd <OBS_SOURCE_PWD> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword>        
&emsp;&emsp;● 检查obs_meta与obs仓库的软件包是否一致	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o <obs_meta_path> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword> --check_meta <bool>        
&emsp;&emsp;● 检查obs_meta与src-openeuler.yaml中的软件包是否一致	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o <obs_meta_path> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword> --check_yaml <bool>        
&emsp;&emsp;● 软件包代码更新	    
&emsp;&emsp;命令：./openeuler_obs -r <giteeTargetRepoName> -o <obs_meta_path> -b <giteeTargetBranch> -ip <OBS_SOURCE_IP> -suser root -spwd <OBS_SOURCE_PWD> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword>	    
&emsp;&emsp;● obs_meta合规检查              
&emsp;&emsp;命令：./openeuler_obs -cps <bool> -prid <giteePullRequestlid>        	    
&emsp;&emsp;● 备份并更新二进制仓库中软件包的二进制	    
&emsp;&emsp;命令1：./openeuler_obs -up <bool> -p <obs_project_name> -repo <repo_name> -arch <arch_name> -rsip <OBS_BACKEND_IP> -rsu root -rsup <OBS_BACKEND_PWD> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword>（归档指定obs仓库中所有软件包的二进制）	    
&emsp;&emsp;命令2：./openeuler_obs -up <bool> -p <obs_project_name> -repo <repo_name> -arch <arch_name> -rsip <OBS_BACKEND_IP> -rsu root -rsup <OBS_BACKEND_PWD> -guser <GiteeCloneUserName> -gpwd <GiteeClonePassword> --pkglist <pkgs>（归档指定obs仓库中一个或多个软件包的二进制）	            

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request


#### 码云特技

1.  使用 Readme\_XXX.md 来支持不同的语言，例如 Readme\_en.md, Readme\_zh.md
2.  码云官方博客 [blog.gitee.com](https://blog.gitee.com)
3.  你可以 [https://gitee.com/explore](https://gitee.com/explore) 这个地址来了解码云上的优秀开源项目
4.  [GVP](https://gitee.com/gvp) 全称是码云最有价值开源项目，是码云综合评定出的优秀开源项目
5.  码云官方提供的使用手册 [https://gitee.com/help](https://gitee.com/help)
6.  码云封面人物是一档用来展示码云会员风采的栏目 [https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)
