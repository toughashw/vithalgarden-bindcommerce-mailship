sudo chmod 755 api_orders.service
sudo chmod 755 api_products.service
sudo chmod 755 api_tracking.service

sudo cp api_orders.service /etc/systemd/system/
sudo cp api_products.service /etc/systemd/system/
sudo cp api_tracking.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable api_orders.service
sudo systemctl enable api_products.service
sudo systemctl enable api_tracking.service

sudo systemctl start api_orders.service
sudo systemctl start api_products.service
sudo systemctl start api_tracking.service

sudo systemctl status api_orders.service
sudo systemctl status api_products.service
sudo systemctl status api_tracking.service
