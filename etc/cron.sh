#!/bin/sh

vnstati -t -c 15 -i eth0 -o /srv/guildbit/app/static/img/info/vnstat_top10.png
sleep 1
vnstati -s -c 15 -i eth0 -o /srv/guildbit/app/static/img/info/vnstat_summary.png
sleep 1
vnstati -m -c 15 -i eth0 -o /srv/guildbit/app/static/img/info/vnstat_monthly.png
sleep 1
vnstati -d -c 15 -i eth0 -o /srv/guildbit/app/static/img/info/vnstat_daily.png
sleep 1
vnstati -h -c 15 -i eth0 -o /srv/guildbit/app/static/img/info/vnstat_hourly.png
sleep 1
exit 0
