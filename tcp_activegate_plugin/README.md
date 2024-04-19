## TCP Network Connections
Esta extensión cuenta la cantidad de conexiones en estado "established" y "time wait" para un patron de búsqueda dado.

Métricas:

* TCP Connectivity - Count Established: ext:tech.network.tcp.established
* TCP Connectivity - Count Time Wait: ext:tech.network.tcp.time_wait 

Logs:
```
sudo tail -f /var/log/dynatrace/supportarchive/remotepluginmodule/log/remoteplugin/custom.remote.python.networkconnections/NetworkConnectionsPluginRemote.log

```
