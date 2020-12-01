# openeuler-obs

#### 介绍
Open build service system for openEuler community.

#### 软件架构
软件架构说明
![输入图片说明](https://images.gitee.com/uploads/images/2020/1201/225845_f7674b15_6525505.png "Snipaste_2020-12-01_22-44-19.png")
#### 功能列表
| 序号   | 功能  | 详细描述  |
|----|---|---|
|  1  | 创建obs仓库 | 根据[obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件创建obs空仓或obs已有仓库的备份仓库   |
|  2  | 删除obs仓库 | [obs_meta/OBS_PRJ_meta](https://gitee.com/src-openeuler/obs_meta/tree/master/OBS_PRJ_meta)目录下的meta文件被删除，则删除对应的obs仓库  |
|  3  | 创建obs仓库软件包  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，在obs对应仓库中创建软件包及软件包下的_service文件  |
|  4  | 删除obs仓库软件包  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，删除obs对应仓库中的软件包  |
|  5  | 修改obs仓库软件包的_service  | 根据[obs_meta](https://gitee.com/src-openeuler/obs_meta)的提交记录，修改obs对应仓库中创建软件包的_service文件  |
|  6  | 软件包检查 | 根据[community/repository](https://gitee.com/openeuler/community/tree/master/repository)/目录下的src-openeuler.yam文件及[obs_meta](https://gitee.com/src-openeuler/obs_meta)对obs仓库的软件包进行检视，补充缺少的软件包、删除码云上不存在的软件包  |
|  7  | 软件包代码更新 | 将码云软件包仓库的代码同步到obs仓库，设置同步开关(开关打开：正常同步;开关关闭：代码不同步，如需同步则后续人工同步) |


#### 使用说明

1.  xxxx
2.  xxxx
3.  xxxx

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
