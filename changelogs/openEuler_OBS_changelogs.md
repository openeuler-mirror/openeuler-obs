# openEuler Open Build Service Change Logs

## 背景
为规范openEuler OBS系统管理，让每一次变更有迹可循，特制定该变更记录表，用于记录对OBS系统做出的每一次配置变更。包括系统硬件配置变更、硬件扩展、软件安装、软件升级、软件变更、相关配置修改等。
	

## 表格填写说明

**变更日期**：发起变更的具体日期，例如：“2021-08-01”  
**变更领域**：描述变更是软件还是硬件，是扩容还是新增; 可选项：“硬件扩展”、“新增软件”、“软件升级”、“软件修改”、“配置变更”等，如果变更不属于上述领域，请知会table责任人新增。  
**变更原因**：描述该变更希望解决什么问题。  
**变更说明**：描述变更的具体内容。如硬件扩展了什么内容、规格多少；或软件安装了什么版本、安装位置、以及安装后配置哪些参数等。  
**责任人**：描述该变更发起者。  
**是否涉及存档**：该变更如果是软件修改或配置变更，通常会有文档或代码修改，修改前后的配置文档或代码对比需要存档，以便后续追溯。“是”或“否”  
**配置文件或代码路径**：如果“是否涉及存档”中填选“是”，则需要在当前仓库该Change Log Table的同级目录下以变更名称新建文件夹来保存相关的变更文档。  

## 变更记录

|序号|变更时间|变更领域|变更原因|变更说明|责任人|是否涉及存档|配置文件或代码路径|
|--|--|--|--|--|--|--|--|
| 1 | 2021-08-06 | 硬件扩展|OBS构建时长优化（测试）|新增home backend节点。该节点新增完成后用于配置openEuler：Mainline 和openEuler-Mainline-copy工程。所有worker节点都注册到给server节点|曹志  |否|NULL|
| 2 |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |

