;
; BIND data file for example.com
; 本機 BIND DNS 專案 - 自訂 Zone 範例
;

$TTL    3600
$ORIGIN example.com.

@       IN      SOA     ns1.example.com. admin.example.com. (
                        2026020201      ; Serial (YYYYMMDDNN)
                        3600            ; Refresh
                        1800            ; Retry
                        604800          ; Expire
                        86400           ; Minimum TTL
                        )

        IN      NS      ns1.example.com.
        IN      NS      ns2.example.com.

        IN      A       192.0.2.1
www     IN      A       192.0.2.1
ns1     IN      A       192.0.2.1
ns2     IN      A       192.0.2.1

        IN      MX      10 mail.example.com.
mail    IN      CNAME   www.example.com.
@       IN      TXT     "v=spf1 mx a ~all"
