# obs构建历史数据同步
## 安装fluentd
```shell script
yum install ruby
yum install ruby-dev
yum install gem

# 安装不上可尝试修改ruby源 
# gem source -a https://gems.ruby-china.com

gem install fluentd
gem install json

fluent-gem install fluent-plugin-kafka
```

````shell script
# 目录下生产配置文件/etc/fluentd/fluent.conf
fluentd --setup /etc/fluentd
````

## fluent配置

> fluent.conf

```
# openEuler:Mainline
<source>
    @type tail
    path /srv/obs/build/openEuler:Mainline/standard_x86_64/x86_64/:jobhistory,/srv/obs/build/openEuler:Mainline/standard_aarch64/aarch64/:jobhistory
    pos_file /srv/obs/build/fluentd_pos_file/openEuler:Mainline
    tag obs_job_history.openEuler:Mainline
    refresh_interval 60s
    read_from_head true
    <parse>
        @type regexp
        expression /^(?<package>[^|]*)\|(?<rev>[^|]*)\|(?<srccmd5>[^|]*)\|(?<versrel>[^|]*)\|(?<bcnt>[^|]*)\|(?<readytime>[^|]*)\|(?<starttime>[^|]*)\|(?<endtime>[^|]*)\|(?<code>[^|]*)\|(?<uri>[^|]*)\|(?<workerid>[^|]*)\|(?<hostarch>[^|]*)\|(?<reason>[^|]*)\|(?<verifymd5>[^|]*)$/
    </parse>
</source>

# filter
<filter obs_job_history.**>
    @type record_transformer
    <record>
        project ${tag_parts[1]}
        duration ${record["endtime"] - record["starttime"]}
        fluentd_time ${time}
    </record>
</filter>

# route
<match obs_job_history.**>
    @type kafka2
    brokers 127.0.0.1:9092
    
    <format>
        @type json
    </format>

    <buffer topic>
        @type file
        path /srv/obs/build/fulentd/fluentd_buffer
        flush_interval 3s
    </buffer>
    topic_key topic
    default_topic openeuler_statewall_obs_job_history

    required_acks 1
</match>
```

## 运行fluentd
```shell script
fluentd -c /etc/fluentd/fluentd.conf -d /var/log/fluentd/fluentd.pid -o /var/log/fluentd/fluentd.log
```
