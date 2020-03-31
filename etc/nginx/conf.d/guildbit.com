server {
    listen 80;

    server_name guildbit.com www.guildbit.com *.guildbit.com;

    access_log /dev/stdout;
    error_log /dev/stdout info;
    
    client_max_body_size 5M;

    location / {
        proxy_pass         http://guildbit:8081/;
        proxy_redirect     off;
        proxy_set_header   Host             $http_host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
    }

    location /robots.txt {
        root /opt/static;
    }

    location /favicon.ico {
        root /opt/static;
    }

    location /BingSiteAuth.xml {
        root /opt/static;
    }

    location /sitemap.xml {
        root /opt/static;
    }
}

server {
    listen 80;

    server_name flower.guildbit.com;

    access_log /dev/stdout;
    error_log /dev/stdout info;
    
    client_max_body_size 5M;

    location / {
        proxy_pass         http://127.0.0.1:5555/;
        proxy_redirect     off;
        proxy_set_header   Host             $http_host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;

	auth_basic            "Restricted";
	auth_basic_user_file  /home/alf/htpasswd;
    }
}
