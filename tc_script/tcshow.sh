#!/bin/bash
while read -r timestamp bandwidth; do
# 设置tc命令read带宽
tc class show dev ens33
# 暂停一段时间，等待到下一个时间戳
sleep 0.5s
done < <(cat high_0)
