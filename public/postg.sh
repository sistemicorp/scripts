#!/usr/bin/env bash

usage () {
  echo "Usage: postg.sh [flags] <command>"
  echo ""
  echo "command:"
  echo "  start                     Start postgres"
  echo ""
  echo "    flags, --restart=, -r   <always|no> (default no) 'always' will start postgres EVERY time the"
  echo "                            computer is booted, which is typically used on a node that"
  echo "                            is in actual deployment."
  echo "                            To disable restart, use 'docker update --restart=no lentedb'"
  echo "                            and then reboot the node."
  echo "           --password=, -p  Password. (default qwerty)"
  echo ""
  echo " stop                       Stop postgres"
  echo ""
}

if [[ $1 == "--help" ]] || [[ $1 == "" ]] ; then
  usage
  exit 0
fi

# set defaults here
flag_restart=no
flag_password=qwerty


start () {
    echo start $flag_restart
    #
    # docker run --rm and --restart commands are exclusive of each other
    #
    if [[ ${flag_password} == "qwerty" ]]; then
        echo WARNING: postgres password is insecure - this better not be production!
    fi
    if [[ ${flag_restart} != "always" ]] && [[ ${flag_restart} != "no" ]]; then
        echo "--restart= must be always or no"
        exit 1
    fi
    mkdir -p postgdata
    docker network create lentenet 2> /dev/null
    if [[ $flag_restart == "always" ]]; then
        docker run --net lentenet \
            --name lentedb \
            --restart=${flag_restart} \
            -v $(pwd)/postgdata:/var/lib/postgresql/data \
            -e POSTGRES_PASSWORD=$flag_password \
            -d \
            postgres:11
    elif [[ $flag_restart == "no" ]]; then
        docker run --net lentenet \
            --name lentedb \
            -v $(pwd)/postgdata:/var/lib/postgresql/data \
            -e POSTGRES_PASSWORD=$flag_password \
            -d \
            --rm \
            postgres:11
    fi
    echo Waiting 5 sec for postgres to start....
    sleep 5
    echo Creating resultbasekeysv1
    docker exec -it lentedb createdb -U postgres resultbasekeysv1 2> /dev/null
}

stop () {
    echo stop
    docker stop lentedb
    docker container rm lentedb
}

handle_command () {
  echo $1
  case $1 in
    start)
      start
      ;;

    stop)
      stop
      ;;

    *)
      echo Unknown Command
      usage
      exit 1
      ;;

  esac
  exit 0
}

# see https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash

while [ "$#" -gt 0 ]; do
  case "$1" in
    -r) flag_restart="$2"; shift 2;;
    -p) flag_password="$2"; shift 2;;

    --restart=*) flag_restart="${1#*=}"; shift 1;;
    --password=*) flag_password="${1#*=}"; shift 1;;
    --restart|--password) echo "$1 requires an argument" >&2; exit 1;;

    -*) echo "unknown option: $1" >&2; exit 1;;
    *) handle_command "$1"; shift 1;;
  esac
done
