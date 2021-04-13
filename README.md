# openeuler-obs

#### 介绍
Open build service system for openEuler community.

#### 软件架构
软件架构说明
![输入图片说明](https://images.gitee.com/uploads/images/2020/1201/225845_f7674b15_6525505.png "Snipaste_2020-12-01_22-44-19.png")
#### 功能列表
| 序号   | 功能  | 详细描述  | 模块名 |
|----|---|---|---|
|  1  | 创建obs仓库 | 根据[obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件创建obs空仓或obs已有仓库的备份仓库   | project_manager.py |
|  2  | 修改obs仓库的Meta配置 | 根据[obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件修改obs仓库的配置   | project_manager.py |
|  3  | 删除obs仓库 | [obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件被删除，则删除对应的obs仓库  | project_manager.py |
|  4  | 创建obs仓库软件包  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，在obs对应仓库中创建软件包及软件包下的_service文件  | package_manager.py |
|  5  | 删除obs仓库软件包  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，删除obs对应仓库中的软件包  | package_manager.py |
|  6  | 修改obs仓库软件包的_service  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，修改obs对应仓库中创建软件包的_service文件  | package_manager.py |
|  7  | 软件包检查 | 根据[community/repository](https://gitee.com/openeuler/community/tree/master/repository)/目录下的src-openeuler.yam文件及[obs_meta](https://gitee.com/src-openeuler/obs_meta)对obs仓库的软件包进行检视，补充缺少的软件包、删除码云上不存在的软件包  | package_manager.py |
|  8  | 软件包检查 | 根据obs仓库及[obs_meta](https://gitee.com/src-openeuler/obs_meta)对obs仓库的软件包进行检视，补充缺少的软件包、删除obs_meta中不存在的软件包 |  package_manager.py |
|  9  | 软件包代码更新 | 将码云软件包仓库的代码同步到obs仓库，设置同步开关(开关打开：正常同步;开关关闭：代码不同步，如需同步则后续人工同步) | gitee_to_obs.py |


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
| obs_project_name   | obs工程名         |
| repo_name          | 二进制仓库名称         |
| arch_name          | 架构名称            |
| giteePullRequestlid | obs_meta仓库未合入的PR号 |
| giteeTargetRepoName | 软件包仓库名称           |
| giteeTargetBranch   | 码云分支名称            |

（1）openeuler_obs.py：用于调度所有功能	    
（2）core目录下	         
&emsp;&emsp;● check_meta_service.py：对obs_meta仓库提交有关新增包PR的内容进行合规检查              
&emsp;&emsp;命令：./openeuler_obs -cps true -prid giteePullRequestlid	    
&emsp;&emsp;● gitee_to_obs.py：同步软件包码云仓库的代码到obs对应的工程	    
&emsp;&emsp;命令：./openeuler_obs -r giteeTargetRepoName -o obs_meta_path -b giteeTargetBranch -ip OBS_SOURCE_IP -suser root -spwd OBS_SOURCE_PWD -guser GiteeCloneUserName -gpwd GiteeClonePassword	    
&emsp;&emsp;● package_manager.py	    
&emsp;&emsp;功能1：根据obs_meta仓库合入的PR对obs工程的软件包进行增删改操作	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o obs_meta_path -ip OBS_SOURCE_IP -suser root -spwd OBS_SOURCE_PWD -guser GiteeCloneUserName -gpwd GiteeClonePassword	    
&emsp;&emsp;功能2：检查obs_meta与obs工程上的软件包是否一致	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o obs_meta_path -guser GiteeCloneUserName -gpwd GiteeClonePassword --check_meta True        
&emsp;&emsp;功能3：检查obs_meta与src-openeuler.yaml中的软件包是否一致	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o obs_meta_path -guser GiteeCloneUserName -gpwd GiteeClonePassword --check_yaml True        
&emsp;&emsp;● project_manager.py：根据obs_meta仓库合入的PR对obs工程进行增删改操作	    
&emsp;&emsp;命令：./openeuler_obs -r obs_meta -o obs_meta_path -ip OBS_SOURCE_IP -suser root -spwd OBS_SOURCE_PWD -guser GiteeCloneUserName -gpwd GiteeClonePassword	    
&emsp;&emsp;● update_obs_repos.py：备份并更新二进制仓库中软件包的二进制	    
&emsp;&emsp;命令1：./openeuler_obs -up True -p obs_project_name -repo repo_name -arch arch_name -rsip OBS_BACKEND_IP -rsu root -rsup OBS_BACKEND_PWD -guser GiteeCloneUserName -gpwd GiteeClonePassword（归档指定obs工程中所有软件包的二进制）	    
&emsp;&emsp;命令2：./openeuler_obs -up True -p obs_project_name -repo repo_name -arch arch_name -rsip OBS_BACKEND_IP -rsu root -rsup OBS_BACKEND_PWD -guser GiteeCloneUserName -gpwd GiteeClonePassword --pkglist pkgs（归档指定obs工程中一个或多个软件包的二进制）	    
&emsp;&emsp;● save.py：提供保存软件包变更信息的功能（供其他脚本调用）	    
（3）config目录下	    
&emsp;&emsp;● config.ini：配置文件	        
（4）common目录下	    
&emsp;&emsp;● common.py：提供对外开放的常用功能，如克隆仓库、远程执行命令、拷贝文件。（供其他脚本调用）	    
&emsp;&emsp;● log_obs.py：提供log打印功能（供其他脚本调用）	    
&emsp;&emsp;● parser_config.py：处理并读取config.ini配置文件中变量的值（供其他脚本调用）        

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
