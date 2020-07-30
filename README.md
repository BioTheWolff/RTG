# Routing Tables Helper - README

A program made by a lover of new technologies, for all networking developers, sysadmins and other people that might find any
use to it.
It aims to ease the creation and calculus of routing tables when working on networks.

## Is it finished yet?

No, the program is only in its first stable release. I'm always hoping to create and innovate more; maybe it won't be
updated for a moment, but it doesn't mean I let it down either.

### Contact info
By mail: biothewolff [at] gmx [dot] fr\
On Discord: BioTheWolff#7708\
You can also find me on these two french Discord servers:
- [Developpeur(euse)s FR](https://discord.gg/8d4ACG5)
- [l4p1n-srv](https://discord.gg/awbUQe4)

## What is it?

The Routing Tables Helper, or RTH, is a program that aims to provide an easy, and quick, way to create routing
tables. Instead of having to create them by hand, using a Virtual Machine (VM) or your own network, and a piece of paper,
this virtual network builder and routing tables generator does it all for you.

The RTH is based on, and uses, another of my programs, [nettools](https://github.com/BioTheWolff/NetTools), a tool for fast networks
and IPs handling and calculus.

# Documentation

## Classes

The main class you'll want to use is the Dispatcher class. You can import it from `rth.core.dispatcher`

The other classes, that each do one part of the work, are the `NetworkCreator`, `Ants` and `RoutingTablesGenerator` classes.
Normally, you won't use them on their own, unless you are willing to do a special action.

## How to use the software

The biggest problem here is how to format the data the right way. 
To generate the routing tables, we will need three things: the subnetworks, the routers and the links. As the computer is no
sentient machine, it needs the links to virtually reconstruct the network and find paths in all this mess of figures and names.

### General flow and usage of the program

This is the easiest and fastest part to read and understand.
You just need to import the Dispatcher, create an instance, `execute()` it the right way and it's all done!

```ignorelang
from rth.core.dispatcher import Dispatcher

inst = Dispatcher()
inst.execute(subnetworks, routers, links)
# And it's all done !

# You can then display the output in the console
inst.display_routing_tables()

# or output it to a file (txt will be the best format for now)
inst.output_routing_tables("D:/Projects/output.txt")
```

### Subnetworks data

The subnetworks data is a dictionary you must provide under this format: `{NAME: CIDR, ...}` meaning putting the names of 
the subnetworks as keys, and their respectives CIDRs in values.

Example: 
```python
subnetworks = {
    'A': "10.0.1.0/24",
    'B': "10.0.2.0/24",
    'C': "10.0.3.0/24"
}
```

NB: if you wish to not give any name to a subnetwork, leave the key as an empty string (`''`) and it will automatically be 
named `<Untitled Network#ID:{ID HERE}>` (with `{ID HERE}` being the unique ID of the network)

### Routers data

The routers data is also a dictionary, which resembles the subnetworks data. The only difference is the value you must give;
the format is `{NAME: HAS_INTERNET_CONNECTION, ...}`. The `HAS_INTERNET_CONNECTION` value **must be either True or None**.
`True` means the router is connected to internet, and `None` means it doesn't.

Example:
```python
routers = {
    0: True,
    1: None,
    2: None,
    3: None
}
``` 

**WARNING:** In this current version, only **ONE** router should have the internet connection. It will throw an exception if
more or less than one are set with an internet connection.

The router with the internet connection will be called "master router" below.

### Links data

The links data is the most important, and also the trickiest to format. The format is
`{ROUTER_NAME: {SUBNETWORK_NAME: IP, ...}, ...}`. So, to explain it more literally, you must make a dictionary of the 
connected subnetworks, and the IP at which the router is connected onto the subnetwork, for each router.

The `IP` value can be either an IPv4, or `None`. If `None` is given, the program will automatically assign an IP for the router,
which will be the first available address starting from the END of the subnetwork range.

Example:
```python
links = {
    0: {
        "A": "10.0.1.200"
    },
    1: {
        "A": None,
        "C": "10.0.3.254"
    },
    2: {
        "A": "10.0.1.253",
        "B": "10.0.2.253"
    },
    3: {
        "B": "10.0.2.252",
        "C": None
    }
}
```

### Now to combine it all into an example

```python
from rth.core.dispatcher import Dispatcher

subnetworks = {
    'A': "10.0.1.0/24",
    'B': "10.0.2.0/24",
    'C': "10.0.3.0/24"
}

routers = {
    0: True,
    1: None,
    2: None,
    3: None
}

links = {
    0: {
        "A": "10.0.1.200"
    },
    1: {
        "A": None,
        "C": "10.0.3.254"
    },
    2: {
        "A": "10.0.1.253",
        "B": "10.0.2.253"
    },
    3: {
        "B": "10.0.2.252",
        "C": None
    }
}

inst = Dispatcher()
inst.execute(subnetworks, routers, links)
```

## Hidden choices, and output formatting

### Hidden choices and impact on paths

This title may be a bit weird, but it will become clear in a second. The program, when it encounters several possible ways
to get from a subnetwork to another, will have to make a choice. Therefore, the path followed by the program, which will be 
of course visible on the routing tables at the end might disturb you. So, in order to clear doubts and help the users find the
path faster, I included a "hops" section in the output.

It looks like this:
```ignorelang
----- HOPS -----
From subnetwork A to subnetwork B: router 2
From subnetwork A to subnetwork C: router 2 > router 1
From subnetwork A to subnetwork D: router 2 > router 1 > router 3
From subnetwork B to subnetwork A: router 2

...
(I only show a small amount here, even though in reality there are more lines)
```

It will help you see which path has been taken.

### Output formatting

The output of the routing tables is not a table, as you might expect. For now, at least.
It currently looks like this:

```ignorelang
----- ROUTING TABLES -----
Router MyRouter
  - 192.168.0.0/24      : 192.168.0.254 via 192.168.0.254
  - 192.168.1.0/24      : 192.168.1.254 via 192.168.1.254
  - 0.0.0.0/0           : 192.168.1.253 via 192.168.1.254
  - 10.0.0.0/24         : 192.168.0.253 via 192.168.0.254
  - 10.0.1.0/24         : 192.168.1.253 via 192.168.1.254
```

As you may have guessed, it is formatted as `DESTINATION NETWORK : GATEWAY via INTERFACE`. The master router route
(so the way out of the local network) is always `0.0.0.0/0` in the output.