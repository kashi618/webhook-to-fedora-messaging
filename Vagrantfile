# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.manage_guest = true

  config.vm.define "w2fm" do |w2fm|
    w2fm.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/40/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-libvirt.x86_64-40-1.14.vagrant.libvirt.box"
    w2fm.vm.box = "f40-cloud-libvirt"
    w2fm.vm.hostname = "w2fm.tinystage.test"

    w2fm.vm.synced_folder '.', '/vagrant', disabled: true
    w2fm.vm.synced_folder ".", "/home/vagrant/webhook-to-fedora-messaging", type: "sshfs"


    w2fm.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 2
      libvirt.memory = 2048
    end

    w2fm.vm.provision "ansible" do |ansible|
      ansible.playbook = "devel/ansible/playbook.yml"
      ansible.config_file = "devel/ansible/ansible.cfg"
      ansible.verbose = true
    end
  end
end
