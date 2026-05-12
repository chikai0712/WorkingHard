;
; BIND data file for example.com
; Multi-NS Project - Zone File Template
;

$TTL    3600        ; 1 hour default TTL
$ORIGIN example.com.

@       IN      SOA     ns1.example.com. admin.example.com. (
                        2025011701      ; Serial (YYYYMMDDNN)
                        3600            ; Refresh (1 hour)
                        1800            ; Retry (30 minutes)
                        604800          ; Expire (1 week)
                        86400           ; Minimum TTL (1 day)
                        )

        ; Name Servers
        IN      NS      ns1.example.com.
        IN      NS      ns2.example.com.

        ; A Records
        IN      A       192.0.2.1
www     IN      A       192.0.2.1
ns1     IN      A       192.0.2.1
ns2     IN      A       192.0.2.1

        ; MX Records (Mail Exchange)
        IN      MX      10 mail.example.com.

        ; CNAME Records
mail    IN      CNAME   www.example.com.

        ; TXT Records
        IN      TXT     "v=spf1 mx a ~all"

