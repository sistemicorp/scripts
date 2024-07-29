Cloud
#####

Lente running on the (GCP) Cloud.


.. contents::
   :local:


GCP
***

Lente should be able to run any cloud but GCP was picked as a first example because they
have a free tier that is free for "life", rather than one year like some of the more popular others.

**The instructions to be presented are certainly not the only way to put Lente on the cloud, and
given the security issues around the Cloud, you should get an expert opinion to set this up.**

There are two ways to structure Lente on the Cloud (GCP),

* Lente and Postgres running on the same instance
* Lente running on a VM, and Postgres running as an SQL

Running both Lente and Postgres on one VM is easier to setup, and is basically the same setup
as when you create a Lente on a local machine.  The CONS of doing it this way is that the Postgres DB
of your results are tied to the instance, you have to keep the instance running or else you will lose
all your data.  You may not be able to expand the VM Instance disk size if you fill it up.

Running the Postgres as a SQL resource is not that much more difficult to set up in the GCP dashboard.
The extra step is that you have to specifically set the Postgres SQl to ALLOW connections from the VM.  There
is in fact an online wizard that guides you thru the process.  Postgres as a separate resource also
enables access to several Google SQL tools, for example, backups, maintenance, and security.

For a production environment, if you choose to have Lente/Postgres in the cloud, the recommended
approach is to use Postgres as a separate resource from the VM running Lente.


Lente/Postgres On Instance VM
=================================

Log into your Google Cloud Account.

Create an instance VM and use a Ubuntu 18.04 Minimum image.

Traffic to/from the GCP node needs to be allowed by the Firewall,

::

    VPC Network -> Firewall Rules
    Name            Type	Targets	        Filters	                Protocols / ports	    Action	Priority	Network
    lente-egress    Egress  Apply to all	IP ranges: 0.0.0.0/0    tcp:6600    udp:6600    Allow   1000        default
    lente-ingress   Ingress Apply to all    IP ranges: 0.0.0.0/0    tcp:6600    udp:6600    Allow   1000        default

**The above Firewall rules allow connection to Lente from any external IP.  You should instead limit access to Lente
to your domain for extra security.**

Open an SSH to the VM and run these commands, which will install Docker, these are copied from https://docs.docker.com/install/linux/docker-ce/ubuntu/

::

    sudo apt-get update
    sudo apt-get install \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository \
       "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
       $(lsb_release -cs) \
       stable"
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker your-user # and then REBOOT!

After you have rebooted, open a new SSH terminal.
Run these commands to install `scripts`,

::

    mkdir ~/git
    cd ~/git
    git clone https://github.com/sistemicorp/scripts.git


Follow `these <lente_demo.html#Postgres>`__ instructions to start postgres server.


Run the Lente start script

::

    cd ~/git/scripts/public
    ./lente.sh --restart=always start
