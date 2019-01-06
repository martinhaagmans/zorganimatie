1. Maak droplet: 1 vCPU, 1GB RAM, 25GB HD

2. [Setup Server]( https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-16-04) 
    
    * SSH-key bij dropletcreatie opgeven is makkelijker.

3. [Install Apache](https://www.digitalocean.com/community/tutorials/how-to-install-linux-apache-mysql-php-lamp-stack-on-ubuntu-16-04)
    * Alleen stap 1
    * Verwijder standaard apache pagina: 
        ```
        sudo a2dissite 000-default.conf
        service apache2 restart
        ```

4. [Deploy flask app](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)

    ```
    sudo chown -R www-data:www-data zorganimatie
    ```

MOD WSGI MOET VOOR PYTHON3
sudo apt-get install libapache2-mod-wsgi-py3

Te installeren: 

* pip
* flask
* kijksluiter app
