#!/usr/bin/env bash

usage () {
  echo "Usage: lente.sh [flags] <command>"
  echo ""
  echo "command:"
  echo "  start                     Start Sistemi Lente"
  echo ""
  echo "    flags, --restart=, -r   <always|no> (default no) 'always' will start Sistemi Lente EVERY time the"
  echo "                            computer is booted, which is typically used on a node that"
  echo "                            is in actual deployment."
  echo "                            To disable restart, use 'docker update --restart=no lente'"
  echo "                            and then reboot the node."
  echo ""
  echo "  update                    Update the docker images, requires internet connection."
  echo "                            You will need to restart Lente with the start command."
  echo ""
  echo "  stop                      Stop Lente"
  echo ""
}

if [[ $1 == "--help" ]] || [[ $1 == "" ]] ; then
  usage
  exit 0
fi

# set defaults here
flag_restart=no

start () {
    echo restart Lente: $flag_restart
    #
    # docker run --rm and --restart commands are exclusive of each other
    #
    if [[ ${flag_restart} != "always" ]] && [[ ${flag_restart} != "no" ]]; then
        echo "--restart= must be always or no"
        exit 1
    fi
    docker stop lente 2> /dev/null
    docker rm lente 2> /dev/null
    if [[ $flag_restart == "always" ]]; then
        docker run -d \
            --network=host \
            --hostname=${HOSTNAME} \
            --restart=${flag_restart} \
            -p 6595:6595 \
            -v $(pwd):/app/public \
            --name lente \
            sistemicorp/lente
    elif [[ $flag_restart == "no" ]]; then
        docker run -d \
            --network=host \
            --hostname=${HOSTNAME} \
            -p 6595:6595 \
            -v $(pwd):/app/public \
            --name lente \
            --rm \
            sistemicorp/lente
    fi
}

docker_pull () {
    echo docker pull latest
    docker pull sistemicorp/lente:latest
    docker update --restart=no lente
    echo Stopping Lente...
    docker stop lente
    docker container rm lente
    echo
    echo Now restart Lente: ./lente.sh --restart=always start
}

stop () {
    echo Stopping Lente...
    docker update --restart=no lente
    docker stop lente
    docker container rm lente
}

handle_command () {
  case $1 in
    start)
      start
      ;;

    update)
      docker_pull
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

    --restart=*) flag_restart="${1#*=}"; shift 1;;
    --restart) echo "$1 requires an argument" >&2; exit 1;;
#    --restart|--pidfile) echo "$1 requires an argument" >&2; exit 1;;  example of adding more

    -*) echo "unknown option: $1" >&2; exit 1;;
    *) handle_command "$1"; shift 1;;
  esac
done
