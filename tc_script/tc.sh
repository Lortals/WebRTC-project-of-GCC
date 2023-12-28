#!/bin/bash

# 清除现有的队列规则和过滤规则
tc qdisc del dev ens33 root

#add rules
tc qdisc add dev ens33 root tbf rate 500Kbit latency 50ms burst 15kb
# 读取数值序列文件
while read -r timestamp bandwidth; do
 # 设置tc命令来改变带宽
tc qdisc change dev ens33 root tbf rate "$bandwidth"mbit latency 50ms burst 15kb
# 暂停一段时间，等待到下一个时间戳
DATE=`date '+%Y%m%d-%H%M%S'`

LogNameDATE=`date '+%Y%m%d'`

echo "———————————————–" >> tcbandwidth.log
echo "BACKUP DATE:" $(date +"%H:%M:%S.%N") >> tcbandwidth.log
echo "bandwidth:" $bandwidth >> tcbandwidth.log
echo "———————————————– " >> tcbandwidth.log
sleep 0.5s
done < <(cat 9)


# 恢复默认带宽设置
tc qdisc del dev ens33 root
