#!/usr/bin/env bash

script_dir=$(dirname $0)
for dir in "data" "sessions"; do 
    rm -rf $script_dir/$dir
    cp -r /var/www/SecretSanta/SecretSanta/$dir $script_dir/
    sudo chown www-data /var/www/SecretSanta/SecretSanta/$dir
done
sudo rsync -vaz * /var/www/SecretSanta/SecretSanta/
sudo service apache2 restart
