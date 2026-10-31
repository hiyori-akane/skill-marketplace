#!/bin/zsh
# usage: scripts/run.sh <name> <outdir> <command...>
# 実行時間とピークメモリ(/usr/bin/time -l)を logs/<name>.log に記録する
name=$1; outdir=$2; shift 2
mkdir -p "$outdir" logs
log=logs/$name.log
{ echo "# $(date '+%F %T') $name"; echo "\$ $*"; } > $log
/usr/bin/time -l "$@" >> $log 2>&1
rc=$?
echo "exit=$rc" >> $log
grep -E 'real|maximum resident|peak memory footprint' $log | tail -3
exit $rc
