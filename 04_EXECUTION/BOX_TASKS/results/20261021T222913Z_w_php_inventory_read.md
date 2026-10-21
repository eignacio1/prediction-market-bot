# Box task `php_inventory_read` — 20261021T222913Z_w_php_inventory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T222913Z_w_php_inventory_read.toml`
- note: Window: DigitalOcean PHP RCE notice 2026-10-21 - is PHP on the box?
- ran: 2026-10-21T22:29:33Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `echo '--- php binaries'; (command -v php php-fpm php-cgi 2>/dev/null; ls /usr/bin/php* /usr/sbin/php* 2>/dev/null) || true; echo '--- php packages'; (dpkg -l 2>/dev/null | grep -i -E '^ii +(php|libapache2-mod-php)' || echo 'no php packages'); echo '--- php processes'; (pgrep -a -f 'php' | grep -v pg`

```
--- php binaries
/usr/sbin/phpcalls-bpfcc
/usr/sbin/phpflow-bpfcc
/usr/sbin/phpstat-bpfcc
--- php packages
no php packages
--- php processes
none running
--- web servers
no web server packages
--- listening tcp
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess                                                    
LISTEN 0      4096   127.0.0.53%lo:53        0.0.0.0:*    users:(("systemd-resolve",pid=3783568,fd=15))             
LISTEN 0      5          127.0.0.1:8050      0.0.0.0:*    users:(("python3",pid=3827993,fd=3))                      
LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*    users:(("sshd",pid=3455917,fd=3),("systemd",pid=1,fd=108))
LISTEN 0      4096      127.0.0.54:53        0.0.0.0:*    users:(("systemd-resolve",pid=3783568,fd=17))             
LISTEN 0      4096            [::]:22           [::]:*    users:(("sshd",pid=3455917,fd=4),("systemd",pid=1,fd=109))
--- os
PRETTY_NAME="Ubuntu 24.04.3 LTS"

```
