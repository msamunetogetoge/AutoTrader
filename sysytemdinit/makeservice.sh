#!bin/bash
sudo cp /home/pi/AutoTrader/sysytemdinit/AutoTrader.service /etc/systemd/system
sudo chown root:root /etc/systemd/system/AutoTrader.service
sudo chmod 644 /etc/systemd/system/AutoTrader.service

sudo cp /home/pi/AutoTrader/systemdint/StartStream.service /etc/systemd/system
sudo chown root:root /etc/systemd/system/StartStream.service
sudo chmod 644 /etc/systemd/system/StartStream.service

sudo mkdir -p /opt/AutoTrader/bin
sudo chmod 755 /opt/AutoTrader/bin
sudo cp /home/pi/AutoTrader/sysytemdinit/autoexec.sh /opt/AutoTrader/bin
sudo chown root:root /opt/AutoTrader/bin/autoexec_at.sh
sudo chmod 755 /opt/AutoTrader/bin/autoexec_at.sh

sudo mkdir -p /opt/StartStream/bin
sudo chmod 755 /opt/StartStream/bin
sudo cp /home/pi/AutoTrader/sysytemdinit/autoexec.sh /opt/StartStream/bin
sudo chown root:root /opt/StartStream/bin/autoexec_ss.sh
sudo chmod 755 /opt/StartStream/bin/autoexec_ss.sh

sudo systemctl daemon-reload
sudo bash /home/pi/AutoTrader/dbinit.sh
sudo systemctl enable AutoTrader.service
sudo systemctl enable StartStream.service
sudo systemctl start StartStream
sudo systemctl start AutoTrader
sudo systemctl start 