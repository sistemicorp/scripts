#!/bin/bash

usage () {
  echo "Usage: prism.sh [flags] <command>"
  echo ""
  echo "command:"
  echo "  start                     Start Prism"
  echo ""
  echo "    flags, --server=, -s    (REQUIRED) Lente IP address. Use 'none' if no Lente."
  echo "           --hostname=, -h  Specify an alternative hostname for this computer (default $(hostname))"
  echo "           --restart=, -r   <always|no> (default no) 'always' will start Lente EVERY time the"
  echo "                            computer is booted, which is typically used on a node that"
  echo "                            is in actual deployment."
  echo "                            To disable restart, use 'docker update --restart=no prism'"
  echo "                            and then reboot the node."
  echo ""
  echo "  update                    Update the docker image, requires internet connection."
  echo "                            You will need to restart Prism with the start command."
  echo ""
}

if [[ $1 == "--help" ]] || [[ $1 == "" ]] ; then
  usage
  exit 0
fi

# set defaults here
flag_server_ip=not_specified
flag_hostname=$(hostname)
flag_restart=no

function valid_ip() {
    local  ip=$1
    local  stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip=($ip)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 \
            && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
        stat=$?
    fi
    return $stat
}

start () {
    # echo start Prism: $flag_restart $flag_hostname $flag_server_ip
    #
    # docker run --rm and --restart commands are exclusive of each other
    #
    if [[ $flag_server_ip == "not_specified" ]]; then
        echo "Lente IP address is required flag (--server)"
        exit 1
    elif [[ $flag_server_ip == "none" ]]; then
        SERVERIP=127.0.0.1
    else
        if valid_ip $flag_server_ip; then
            SERVERIP=${flag_server_ip}
        else
            echo "IP address is valid, please check"
            exit 1
        fi
    fi
    if [[ ${flag_restart} != "always" ]] && [[ ${flag_restart} != "no" ]]; then
            echo "--restart= must be always or no"
            exit 1
    fi
    echo Using Lente IP = $SERVERIP
    docker stop prism 2> /dev/null
    docker rm prism 2> /dev/null
    if [[ $flag_restart == "always" ]]; then
        docker run -d \
            --restart=${flag_restart} \
            -e SERVERIP=${SERVERIP} \
            --hostname=${flag_hostname} \
            -p 6800:6800 \
            -v $(pwd):/app/public \
            -v /dev:/dev \
            --device=/dev \
            --name prism \
            sistemicorp/prism
    elif [[ $flag_restart == "no" ]]; then
        docker run -d \
            -e SERVERIP=${SERVERIP} \
            --hostname=${flag_hostname} \
            -p 6800:6800 \
            -v $(pwd):/app/public \
            -v /dev:/dev \
            --device=/dev \
            --name prism \
            --rm \
            sistemicorp/prism
    fi
}

docker_pull () {
    echo docker pull
    docker pull sistemicorp/prism
    docker update --restart=no prism
    docker stop prism
    docker container rm prism
    echo
    echo Now restart Prism: ./prism.sh --server=? --restart=always start
}

stop () {
    docker update --restart=no prism
    docker stop prism
    docker container rm prism
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
    -h) flag_hostname="$2"; shift 2;;
    -s) flag_server_ip="$2"; shift 2;;

    --restart=*) flag_restart="${1#*=}"; shift 1;;
    --hostname=*) flag_hostname="${1#*=}"; shift 1;;
    --server=*) flag_server_ip="${1#*=}"; shift 1;;
    --restart|--hostname|--server) echo "$1 requires an argument" >&2; exit 1;;

    -*) echo "unknown option: $1" >&2; exit 1;;
    *) handle_command "$1"; shift 1;;
  esac
done

