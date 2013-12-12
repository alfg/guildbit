server {
    listen 80;

    server_name guildbit.com www.guildbit.com *.guildbit.com;

    access_log /var/log/nginx/guildbit.access.log;
    error_log /var/log/nginx/guildbit.error.log;
    
    client_max_body_size 5M;

    location / {
        proxy_pass         http://127.0.0.1:3000/;
        proxy_redirect     off;
        proxy_set_header   Host             $http_host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
    }

    location /robots.txt {
        root /home/alf/http/guildbit.com;
    }

    location /favicon.ico {
        root /home/alf/http/guildbit.com/static;
    }

    location /BingSiteAuth.xml {
        root /home/alf/http/guildbit.com;
    }

    location /sitemap.xml {
        root /home/alf/http/guildbit.com;
    }

    location /static {
        alias /srv/guildbit/app/static/;
    }

    error_page 500 502 504 /50x.html;
    location = /50x.html {
        root   /home/alf/http/guildbit.com/error_pages;
    }

    error_page 403 /403.html;
    location = /403.html {
       root   /home/alf/http/guildbit.com/error_pages;
       allow all;
    }

    error_page 503 @maintenance;
    location @maintenance {
          rewrite ^(.*)$ /error503.html break;
    }
}

server {
    listen 80;

    server_name flower.guildbit.com;

    access_log /var/log/nginx/flower.guildbit.access.log;
    error_log /var/log/nginx/flower.guildbit.error.log;
    
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
