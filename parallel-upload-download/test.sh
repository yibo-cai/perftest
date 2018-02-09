set -e

export ACCESSKEY=${ACCESSKEY:-minio}
export SECRETKEY=${SECRETKEY:-minio123}
export ENDPOINT=${ENDPOINT:-http://127.0.0.1:9000}

logf=/tmp/minio-perf.csv

[ -f $logf ] && { echo $logf exists!; exit 1; }
echo "type,objsz,workers,bandwidth" > $logf


function clear_data()
{
    rm -rf ~/minio/data/ttt
    mkdir ~/minio/data/ttt
}


function do_test()
{
    objsz=$1
    workers=$2

    cmd="CONCURRENCY=$workers BUCKET=ttt ./parallel-put -size $objsz"
    echo $cmd
    bw=`eval $cmd | tee /dev/stderr | grep Bandwidth | sed 's/[^0-9]//g'`
    echo "put,$objsz,$workers,$bw" >> $logf

    cmd="CONCURRENCY=$workers BUCKET=ttt ./parallel-get -size $objsz"
    echo $cmd
    bw=`eval $cmd | tee /dev/stderr | grep Bandwidth | sed 's/[^0-9]//g'`
    echo "get,$objsz,$workers,$bw" >> $logf
}


clear_data

workers_lst="128,256,512,1024"
objsz_lst="262144,1048576,2097152,4194304,8388608"

ifs=$IFS
IFS=,
for objsz in $objsz_lst; do
    for workers in $workers_lst; do
        do_test $objsz $workers
        clear_data
    done
done
IFS=$ifs
