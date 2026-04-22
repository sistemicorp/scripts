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
  echo "  stop                      Stop Prism"
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
flag_instno=""
flag_image="sistemicorp/prism"
flag_network="host"

IP4=$(ip route get 1 | sed -n 's/^.*src \([0-9.]*\) .*$/\1/p')

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
        LENTEIP=127.0.0.1
    else
        if valid_ip $flag_server_ip; then
            LENTEIP=${flag_server_ip}
        else
            echo "IP address is invalid, please check"
            exit 1
        fi
    fi
    if [[ ${flag_restart} != "always" ]] && [[ ${flag_restart} != "no" ]]; then
            echo "--restart= must be always or no"
            exit 1
    fi
    echo Using Lente IP = $LENTEIP
    echo Using Prism Image = $flag_image
    docker stop prism${flag_instno} 2> /dev/null
    docker rm prism${flag_instno} 2> /dev/null
    if [[ $flag_restart == "always" ]]; then
        docker run -d \
            --network=${flag_network}\
            --hostname=${HOSTNAME}${flag_instno} \
            --restart=${flag_restart} \
            -e LENTEIP=${LENTEIP} \
            --hostname=${flag_hostname}${flag_instno} \
            -v $(pwd):/app/public \
            -v /dev:/dev \
            -v /var/run/dbus/:/var/run/dbus/:z \
            --device=/dev \
            --privileged \
            --device /dev/snd \
            --group-add audio \
            --name prism${flag_instno} \
            ${flag_image}
    elif [[ $flag_restart == "no" ]]; then
        docker run -d \
            --network=${flag_network}\
            --hostname=${HOSTNAME}${flag_instno} \
            -e LENTEIP=${LENTEIP} \
            -e HOSTIP=${IP4} \
            --hostname=${flag_hostname}${flag_instno} \
            -v $(pwd):/app/public \
            -v /dev:/dev \
            -v /var/run/dbus/:/var/run/dbus/:z \
            --device=/dev \
            --privileged \
            --device /dev/snd \
            --group-add audio \
            --name prism${flag_instno} \
            --rm \
            ${flag_image}
    fi
}

docker_pull () {
    if [[ "${flag_image}" == *":"* ]]; then
      pull_image=${flag_image}
    else
      pull_image=${flag_image}:latest
    fi
    echo docker pull ${pull_image}...
    docker pull ${pull_image}
    echo "Stopping Prism... (if its running)"
    docker update --restart=no prism${flag_instno}
    docker stop prism${flag_instno}
    docker container rm prism${flag_instno}
    echo
    echo Now restart Prism: ./prism.sh --server=? --restart=always start
}

stop () {
    echo "Stopping Prism... (if its running)"
    docker update --restart=no prism${flag_instno}
    docker stop prism${flag_instno}
    docker container rm prism${flag_instno}
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
    -n) flag_instno="$2"; shift 2;;
    -i) flag_image="$2"; shift 2;;
    -b) flag_network="bridge"; shift 1;;

    --restart=*) flag_restart="${1#*=}"; shift 1;;
    --hostname=*) flag_hostname="${1#*=}"; shift 1;;
    --server=*) flag_server_ip="${1#*=}"; shift 1;;
    --restart|--hostname|--server) echo "$1 requires an argument" >&2; exit 1;;

    -*) echo "unknown option: $1" >&2; exit 1;;
    *) handle_command "$1"; shift 1;;
  esac
done
