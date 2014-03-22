#! /bin/bash

###
# Script to dump database, create tarball, and
# backup to S3. Requires s3cmd and .pgpass to be installed/configured.
# Place provided .pgpass file in home directory and chmod 0600
###

NOW=$(date +"%m-%d-%Y")

echo "Dumping Guildbit database..."
pg_dump -U postgres -h localhost guildbit > /tmp/test.sql
echo "Database dumped to /tmp/ Creating tarball from DB dump..."
tar -cvzf $NOW.tar.gz /tmp/test.sql
echo "Tarball created. Removing dump file..."
rm -rf /tmp/test.sql
echo "Dump file removed. Backing up to S3..."
s3cmd put $NOW.tar.gz s3://guildbit/backups/db/guildbit_$NOW.tar.gz
echo "Backup successfully completed."

exit 0
