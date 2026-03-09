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
flag_instno=""
flag_image="sistemicorp/lente"
flag_network="host"
flag_verbose=""

start () {
    echo restart Lente: $flag_restart
    #
    # docker run --rm and --restart commands are exclusive of each other
    #
    if [[ ${flag_restart} != "always" ]] && [[ ${flag_restart} != "no" ]]; then
        echo "--restart= must be always or no"
        exit 1
    fi
    docker stop lente${flag_instno} 2> /dev/null
    docker rm lente${flag_instno} 2> /dev/null
    if [[ $flag_restart == "always" ]]; then
        docker run -d \
            --network=${flag_network}\
            --hostname=${HOSTNAME}${flag_instno} \
            --restart=${flag_restart} \
            -v $(pwd):/app/public \
            --name lente${flag_instno} \
            ${flag_image} \
	    ${flag_verbose}
    elif [[ $flag_restart == "no" ]]; then
        docker run -d \
            --network=${flag_network}\
            --hostname=${HOSTNAME}${flag_instno} \
            -v $(pwd):/app/public \
            --name lente${flag_instno} \
            --rm \
            ${flag_image} \
	    ${flag_verbose}
    fi
}

docker_pull () {
    if [[ "${flag_image}" == *":"* ]]; then
      pull_image=${flag_image}
    else
      pull_image=${flag_image}:latest
    fi

    echo docker pull ${pull_image}
    docker pull ${pull_image}
    docker update --restart=no lente${flag_instno}
    echo Stopping Lente...
    docker stop lente${flag_instno}
    docker container rm lente${flag_instno}
    echo
    echo Now restart Lente: ./lente.sh --restart=always start
}

stop () {
    echo Stopping Lente...
    docker update --restart=no lente${flag_instno}
    docker stop lente${flag_instno}
    docker container rm lente${flag_instno}
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
    -n) flag_instno="$2"; shift 2;;
    -i) flag_image="$2"; shift 2;;
    -b) flag_network="bridge"; shift 1;;
    -v) flag_verbose="--verbose"; shift 1;;


    --restart=*) flag_restart="${1#*=}"; shift 1;;
    --restart) echo "$1 requires an argument" >&2; exit 1;;
#    --restart|--pidfile) echo "$1 requires an argument" >&2; exit 1;;  example of adding more

    -*) echo "unknown option: $1" >&2; exit 1;;
    *) handle_command "$1"; shift 1;;
  esac
done
