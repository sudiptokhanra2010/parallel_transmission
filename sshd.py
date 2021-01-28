#!/usr/bin/python

"""
Create a network and start sshd(8) on each host.
While something like rshd(8) would be lighter and faster,
(and perfectly adequate on an in-machine network)
the advantage of running sshd is that scripts can work
unchanged on mininet and hardware.
In addition to providing ssh access to hosts, this example
demonstrates:
- creating a convenience function to construct networks
- connecting the host network to the root namespace
- running server processes (sshd in this case) on hosts
"""

import sys

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.node import Node
from mininet.topolib import TreeTopo
from mininet.util import waitListening
from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
	s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )

        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
	h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )
        

        # Add links
	self.addLink( s1, s2, bw=100)
        self.addLink( h1, s1, bw=10)
	self.addLink( h2, s1, bw=10)
	self.addLink( h3, s2, bw=10)
	self.addLink( h4, s2, bw=10)
	

topos = { 'mytopo': ( lambda: MyTopo() ) }


def connectToRootNS( network, switch, ip, routes ):
    """Connect hosts to root namespace via switch. Starts network.
      network: Mininet() network object
      switch: switch to connect to root namespace
      ip: IP address for root namespace node
      routes: host networks to route to"""
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = network.addLink( root, switch ).intf1
    root.setIP( ip, intf=intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        switch = network[ 's1' ]  # switch to use
	
    if not routes:
        routes = [ '10.0.0.0/24' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    info( "*** Waiting for ssh daemons to start\n" )
    for server in network.hosts:
        waitListening( server=server, port=22, timeout=5 )

    info( "\n*** Hosts are running sshd at the following addresses:\n" )
    for host in network.hosts:
        info( host.name, host.IP(), '\n' )
    info( "\n*** Type 'exit' or control-D to shut down network\n" )
    CLI( network )
    for host in network.hosts:
        host.cmd( 'kill %' + cmd )
    network.stop()

if __name__ == '__main__':
    lg.setLogLevel( 'info')
    #net = TreeNet( depth=1, fanout=4 )
    net = Mininet( topo = MyTopo() )
    # get sshd args from the command line or use default args
    # useDNS=no -u0 to avoid reverse DNS lookup timeout
    argvopts = ' '.join( sys.argv[ 1: ] ) if len( sys.argv ) > 1 else (
        '-D -o UseDNS=no -u0' )
    sshd( net, opts=argvopts )
